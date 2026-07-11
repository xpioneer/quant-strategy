import akshare as ak
import pandas as pd
import re
import time
import random
import requests
from datetime import datetime
from app.market.providers.base import BaseDataProvider

class AkShareProvider(BaseDataProvider):
    def fetch_history(self, symbol: str, period: str = 'daily') -> pd.DataFrame:
        """原有的 AKShare 拉取逻辑（带防封禁）"""
        print(f"[INFO] 降级 AKShare 获取 {symbol} ...")
        is_a_share = bool(re.match(r'^\d{6}$', symbol))
        
        # ===== 1. 随机 User-Agent 列表 =====
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        # ===== 2. 给 AKShare 的 requests Session 注入随机 UA =====
        session = requests.Session()
        session.headers.update({
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        
        # Monkey patch: 让 AKShare 内部使用我们的 session
        original_get = requests.get
        requests.get = session.get
        
        try:
            # ===== 3. 确定请求目标 =====
            fetch_targets = []
            if is_a_share:
                if hasattr(ak, "stock_zh_a_hist"):
                    print(f"[INFO] DC AKShare 使用 stock_zh_a_hist 获取 {symbol} ...") 
                    fetch_targets.append({
                        "func": ak.stock_zh_a_hist,
                        "params": {
                            "symbol": symbol,
                            "period": period,
                            "start_date": "19900101",
                            "end_date": datetime.now().strftime("%Y%m%d"),
                            "adjust": "qfq"
                        }
                    })
                # 加新浪兜底
                if hasattr(ak, "stock_zh_a_daily"):
                    sina_code = ("sh" if symbol.startswith("6") else "sz") + symbol
                    print(f"[INFO] Sina AKShare 使用 stock_zh_a_daily 获取 {symbol} ...")
                    fetch_targets.append({
                        "func": ak.stock_zh_a_daily,
                        "params": {
                            "symbol": sina_code,
                            "start_date": "19900101",
                            "end_date": datetime.now().strftime("%Y%m%d"),
                            "adjust": "qfq"
                        }
                    })
            else:
                if hasattr(ak, "stock_us_hist"):
                    fetch_targets.append({
                        "func": ak.stock_us_hist,
                        "params": {
                            "symbol": symbol,
                            "adjust": "qfq",
                            "start_date": "19700101",
                            "end_date": datetime.now().strftime("%Y%m%d")
                        }
                    })
            
            if not fetch_targets:
                raise RuntimeError("No suitable AKShare function found for symbol: " + symbol)
            
            # ===== 4. 带指数退避的重试请求 =====
            last_err = None
            df_raw = None
            
            for target in fetch_targets:
                func = target["func"]
                params = target["params"]
                
                for attempt in range(3):  # 最多重试 3 次
                    try:
                        # ★ 关键：每次请求前随机等待 0.5~1.5 秒
                        time.sleep(random.uniform(0.5, 1.5))
                        df_raw = func(**params)
                        if df_raw is not None and not df_raw.empty:
                            print(f"[INFO] AKShare 成功获取 {symbol} ({len(df_raw)} 条)")
                            break
                            
                    except (ConnectionAbortedError, ConnectionResetError, 
                            requests.exceptions.ConnectionError) as e:
                        last_err = e
                        if attempt < 2:
                            wait_time = (attempt + 1) * 3
                            print(f"[WARN] 连接断开，{wait_time}s 后重试 ({attempt+1}/3)...")
                            time.sleep(wait_time)
                        continue
                        
                    except Exception as e:
                        last_err = e
                        # 非网络错误不重试
                        break
                
                if df_raw is not None and not df_raw.empty:
                    break
            
            if df_raw is None or df_raw.empty:
                if last_err:
                    raise RuntimeError(f"AKShare fetch failed for {symbol}: {last_err}")
                return pd.DataFrame()
            
            # 标准化 AKShare 数据
            df = df_raw.copy()
            if not isinstance(df.index, pd.RangeIndex):
                df = df.reset_index()
            
            # 如果是新浪数据，日期可能在 index 里
            if "date" not in df.columns:
                df = df.rename(columns={df.columns[0]: "date"})
            
            col_map = {}
            candidates = {
                "date": ["date", "日期", "trade_date", "timestamp", "time"],
                "open": ["open", "开盘", "开盘价"],
                "high": ["high", "最高"],
                "low": ["low", "最低"],
                "close": ["close", "收盘", "收盘价", "close_price"],
                "volume": ["volume", "成交量", "vol"],
                "amount": ["amount", "成交额"],
                "amplitude": ["amplitude", "振幅"],
                "pct_change": ["pct_change", "涨跌幅", "change_pct", "pct_chg"],
                "change": ["change", "涨跌额", "price_change"],
                "turnover_rate": ["turnover_rate", "换手率"],
            }
            
            for target, keys in candidates.items():
                for k in keys:
                    if k in df.columns:
                        col_map[target] = k
                        break
                if target not in col_map:
                    for col in df.columns:
                        if col.lower() in [c.lower() for c in keys]:
                            col_map[target] = col
                            break
            
            normalized = pd.DataFrame()
            if "date" in col_map:
                normalized["date"] = pd.to_datetime(df[col_map["date"]])
            else:
                normalized["date"] = pd.to_datetime(df.iloc[:, 0])
            
            for key in ("open", "high", "low", "close", "volume", "amount",
                        "amplitude", "pct_change", "change", "turnover_rate"):
                if key in col_map:
                    normalized[key] = pd.to_numeric(df[col_map[key]], errors="coerce")
                else:
                    normalized[key] = pd.NA
            
            normalized["symbol"] = symbol
            normalized = normalized.dropna(subset=["close"])
            normalized = normalized.sort_values("date").reset_index(drop=True)
            
            # 补充计算派生字段
            if not normalized.empty:
                need_amplitude = normalized["amplitude"].isna().all()
                need_change = normalized["change"].isna().all()
                need_pct = normalized["pct_change"].isna().all()
                
                if need_amplitude or need_change or need_pct:
                    prev_close = None
                    amplitudes, changes, pcts = [], [], []
                    
                    for _, row in normalized.iterrows():
                        if prev_close is None or prev_close == 0:
                            amplitudes.append(pd.NA)
                            changes.append(pd.NA)
                            pcts.append(pd.NA)
                        else:
                            cur_high = row["high"]
                            cur_low = row["low"]
                            cur_close = row["close"]
                            
                            if need_amplitude:
                                amp = (cur_high - cur_low) / prev_close * 100 \
                                    if pd.notna(cur_high) and pd.notna(cur_low) else pd.NA
                                amplitudes.append(amp)
                            
                            if need_change:
                                chg = cur_close - prev_close if pd.notna(cur_close) else pd.NA
                                changes.append(chg)
                            
                            if need_pct:
                                pct = (cur_close - prev_close) / prev_close * 100 \
                                    if pd.notna(cur_close) else pd.NA
                                pcts.append(pct)
                        
                        prev_close = row["close"]
                    
                    if need_amplitude:
                        normalized["amplitude"] = amplitudes
                    if need_change:
                        normalized["change"] = changes
                    if need_pct:
                        normalized["pct_change"] = pcts
                
                if "turnover_rate" not in normalized.columns:
                    normalized["turnover_rate"] = pd.NA
            
            return normalized
            
        finally:
            # 恢复原始的 requests.get，避免影响其他地方
            requests.get = original_get