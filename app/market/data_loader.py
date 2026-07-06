from datetime import datetime, timedelta

import pandas as pd
import re
import akshare as ak
from app.database import SessionLocal
from app.database.models import Kline


class MarketDataLoader:
    def __init__(self):
        self.sample_stocks = [
            {"symbol": "AAPL", "name": "苹果公司", "market": "NASDAQ"},
            {"symbol": "MSFT", "name": "微软", "market": "NASDAQ"},
            {"symbol": "TSLA", "name": "特斯拉", "market": "NASDAQ"},
            {"symbol": "BABA", "name": "阿里巴巴", "market": "NYSE"},
            {"symbol": "000001", "name": "平安银行", "market": "SZ"},
        ]

    def get_stock_list(self, limit: int = 20) -> list[dict]:
        return self.sample_stocks[:limit]

    def get_stock_data(self, symbol: str) -> dict | None:
        for stock in self.sample_stocks:
            if stock["symbol"] == symbol:
                return stock
        return None

    def load_kline_data(self, symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily") -> pd.DataFrame:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        # Step 1: try local DB first by symbol
        session = SessionLocal()
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            has_symbol = session.query(Kline).filter(Kline.symbol == symbol).first()
            if has_symbol:
                db_rows = session.query(Kline).filter(Kline.symbol == symbol, Kline.date >= start_dt, Kline.date <= end_dt).order_by(Kline.date).all()
                data = [{
                    "date": r.date,
                    "symbol": r.symbol,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                    "amount": r.amount,
                    "amplitude": r.amplitude,
                    "pct_change": r.pct_change,
                    "change": r.change,
                    "turnover_rate": r.turnover_rate,
                } for r in db_rows]
                local = True
                return pd.DataFrame(data), local
        finally:
            session.close()

        # Step 2: local DB has no data for this symbol — fetch all available data from AKShare
        try:
            import akshare as ak  # type: ignore
        except Exception as e:
            # akshare not available — surface error
            raise ImportError("akshare is required for remote fetching: " + str(e))

        df_ak = None
        fetch_attempts = []
        # Detect market: A股 if 6 digits, 美股 if alphabetic
        is_a_share = bool(re.match(r'^\d{6}$', symbol))
        try:
            if is_a_share:
                # prefer A-share APIs
                if hasattr(ak, "stock_zh_a_daily"):
                    fetch_attempts.append(("stock_zh_a_daily", ak.stock_zh_a_daily))
                if hasattr(ak, "stock_zh_a_hist"):
                    fetch_attempts.append(("stock_zh_a_hist", ak.stock_zh_a_hist))
                # some akshare versions may expose different helpers
                if hasattr(ak, "stock_zh_a_minute"):
                    fetch_attempts.append(("stock_zh_a_minute", ak.stock_zh_a_minute))
            else:
                # prefer US stock APIs
                if hasattr(ak, "stock_us_daily"):
                    fetch_attempts.append(("stock_us_daily", ak.stock_us_daily))
                if hasattr(ak, "stock_us_spot_em"):
                    fetch_attempts.append(("stock_us_spot_em", ak.stock_us_spot_em))
        except Exception:
            pass

        last_err = None
        fetch_start = "1990-01-01"
        fetch_end = datetime.now().strftime("%Y-%m-%d")
        for name, fn in fetch_attempts:
            try:
                df_ak = fn(symbol=symbol, start_date=fetch_start, end_date=fetch_end)
                if df_ak is not None:
                    break
            except TypeError:
                try:
                    df_ak = fn(symbol)
                    if df_ak is not None:
                        break
                except Exception as e:
                    last_err = e
            except Exception as e:
                last_err = e

        if df_ak is None:
            if last_err:
                raise RuntimeError(f"AKShare fetch attempts failed: {last_err}")
            raise RuntimeError("No AKShare fetch function available in this environment")

        # If AKShare returned empty, return empty DataFrame
        if getattr(df_ak, "empty", False):
            empty = pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume", "amount", "amplitude", "pct_change", "change", "turnover_rate"])
            return empty

        # Normalize AKShare frame to expected columns
        df = df_ak.copy()
        if not isinstance(df.index, pd.RangeIndex):
            df = df.reset_index()

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

        for target in candidates:
            if target not in col_map:
                for col in df.columns:
                    if col.lower() in [c.lower() for c in candidates[target]]:
                        col_map[target] = col
                        break

        normalized = pd.DataFrame()
        if "date" in col_map:
            normalized["date"] = pd.to_datetime(df[col_map["date"]])
        else:
            normalized["date"] = pd.to_datetime(df.iloc[:, 0])

        for key in ("open", "high", "low", "close", "volume", "amount", "amplitude", "pct_change", "change", "turnover_rate"):
            if key in col_map:
                normalized[key] = pd.to_numeric(df[col_map[key]], errors="coerce")
            else:
                normalized[key] = pd.NA

        normalized["symbol"] = symbol
        # normalized["local"] = False
        local = False
        normalized = normalized.dropna(subset=["close"]) if not normalized.empty else normalized
        normalized = normalized.sort_values("date").reset_index(drop=True)

        if not normalized.empty:
            prev_close = None
            amplitude = []
            pct_change = []
            change_amount = []
            for i, row in normalized.iterrows():
                if i == 0 or pd.isna(prev_close) or prev_close == 0:
                    amplitude.append(pd.NA)
                    pct_change.append(pd.NA)
                    change_amount.append(pd.NA)
                else:
                    current_close = row["close"]
                    current_high = row["high"]
                    current_low = row["low"]
                    amplitude.append((current_high - current_low) / prev_close * 100 if pd.notna(current_high) and pd.notna(current_low) else pd.NA)
                    change_amount.append(current_close - prev_close if pd.notna(current_close) else pd.NA)
                    pct_change.append((current_close - prev_close) / prev_close * 100 if pd.notna(current_close) else pd.NA)
                prev_close = row["close"]

            if normalized["amplitude"].isna().all():
                normalized["amplitude"] = amplitude
            if normalized["change"].isna().all():
                normalized["change"] = change_amount
            if normalized["pct_change"].isna().all():
                normalized["pct_change"] = pct_change
            if "turnover_rate" not in normalized.columns:
                normalized["turnover_rate"] = pd.NA

        # Step 3: save fetched data to local DB (replace all existing rows for this symbol)
        session = SessionLocal()
        try:
            if not normalized.empty:
                session.query(Kline).filter(Kline.symbol == symbol).delete(synchronize_session=False)
                to_insert = []
                for _, row in normalized.iterrows():
                    dt = pd.to_datetime(row['date']).to_pydatetime()
                    k = Kline(
                        symbol=symbol,
                        date=dt,
                        open=float(row.get('open') if pd.notna(row.get('open')) else 0.0),
                        high=float(row.get('high') if pd.notna(row.get('high')) else 0.0),
                        low=float(row.get('low') if pd.notna(row.get('low')) else 0.0),
                        close=float(row.get('close') if pd.notna(row.get('close')) else 0.0),
                        volume=float(row.get('volume') if pd.notna(row.get('volume')) else 0.0),
                        amount=float(row.get('amount') if pd.notna(row.get('amount')) else 0.0),
                        amplitude=float(row.get('amplitude') if pd.notna(row.get('amplitude')) else 0.0),
                        pct_change=float(row.get('pct_change') if pd.notna(row.get('pct_change')) else 0.0),
                        change=float(row.get('change') if pd.notna(row.get('change')) else 0.0),
                        turnover_rate=float(row.get('turnover_rate') if pd.notna(row.get('turnover_rate')) else 0.0),
                    )
                    to_insert.append(k)
                if to_insert:
                    session.add_all(to_insert)
            session.commit()
        except Exception as e:
            session.rollback()
            raise RuntimeError('Failed to save AKShare data to DB: ' + str(e))
        finally:
            session.close()

        return normalized[(normalized['date'] >= start_dt) & (normalized['date'] <= end_dt)].reset_index(drop=True), local

    def delete_symbol(self, symbol: str, period: str = "daily") -> pd.DataFrame:
        """
        Force update all historical Kline data for `symbol`.
        Deletes existing local rows then fetches fresh data and saves to DB.
        Returns the fresh DataFrame.
        """
        session = SessionLocal()
        try:
            session.query(Kline).filter(Kline.symbol == symbol).delete(synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise RuntimeError("Failed to delete existing Kline rows: " + str(e))
        finally:
            session.close()

        # After deletion, load_kline_data will fetch remotely and save to DB.
        return "delete done"
    
    def load_kline_data_v2(self, symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily") -> tuple[pd.DataFrame, bool]:
        """
        加载 K 线数据。
        返回 (DataFrame, is_local)，is_local=True 表示数据来自本地数据库。
        """
        # ---------- 1. 处理日期参数 ----------
        start_dt = pd.to_datetime(start_date) if start_date else None
        end_dt   = pd.to_datetime(end_date)   if end_date   else None

        session = SessionLocal()
        try:
            # ---------- 2. 尝试从本地数据库读取 ----------
            query = session.query(Kline).filter(Kline.symbol == symbol)
            has_symbol = query.first()
            print(f"has_symbol: {has_symbol}")
            if has_symbol:
                # 如果指定了日期范围，按日期过滤
                if start_dt is not None:
                    query = query.filter(Kline.date >= start_dt)
                if end_dt is not None:
                    query = query.filter(Kline.date <= end_dt)
                
                db_rows = query.order_by(Kline.date).all()
                
                if db_rows:
                    # 本地有数据，直接返回
                    local = True
                    data = [{
                        "date": r.date,
                        "symbol": r.symbol,
                        "open": r.open,
                        "high": r.high,
                        "low": r.low,
                        "close": r.close,
                        "volume": r.volume,
                        "amount": r.amount,
                        "amplitude": r.amplitude,
                        "pct_change": r.pct_change,
                        "change": r.change,
                        "turnover_rate": r.turnover_rate,
                    } for r in db_rows]
                    return pd.DataFrame(data), local
            else:
                # ---------- 3. 本地无数据，从远程拉取全量数据 ----------
                local = False
                df_remote = self._fetch_full_history_from_akshare(symbol, period)
                
                if df_remote.empty:
                    # 远程也没数据，返回空 DataFrame
                    empty = pd.DataFrame(columns=[
                        "date", "symbol", "open", "high", "low", "close",
                        "volume", "amount", "amplitude", "pct_change", "change", "turnover_rate"
                    ])
                    return empty, local
                
                # ---------- 4. 保存到本地数据库（先删后插） ----------
                self._save_kline_to_db(session, symbol, df_remote)
                
                # ---------- 5. 按请求的日期范围筛选返回 ----------
                result_df = df_remote.copy()
                if start_dt is not None:
                    result_df = result_df[result_df['date'] >= start_dt]
                if end_dt is not None:
                    result_df = result_df[result_df['date'] <= end_dt]
                
                return result_df.reset_index(drop=True), local
        
        finally:
            session.close()


    def _fetch_full_history_from_akshare(self, symbol: str, period: str = 'daily') -> pd.DataFrame:
        """
        从 AKShare 拉取某只股票的【全部历史数据】（1990-01-01 至今）。
        返回标准化后的 DataFrame，列名统一为：
        date, symbol, open, high, low, close, volume, amount, amplitude, pct_change, change, turnover_rate
        """
        # try:
        #     import akshare as ak
        # except ImportError as e:
        #     raise ImportError("akshare is required for remote fetching: " + str(e))
        
        # 判断市场
        is_a_share = bool(re.match(r'^\d{6}$', symbol))
        
        fetch_targets = []
        if is_a_share:
            # if hasattr(ak, "stock_zh_a_daily"):
            #     fetch_targets.append(ak.stock_zh_a_daily)
            if hasattr(ak, "stock_zh_a_hist"):
                fetch_targets.append(ak.stock_zh_a_hist)
        else:
            if hasattr(ak, "stock_us_daily"):
                fetch_targets.append(ak.stock_us_daily)
            # if hasattr(ak, "stock_us_spot_em"):
            #     fetch_targets.append(ak.stock_us_spot_em)
        
        if not fetch_targets:
            raise RuntimeError("No suitable AKShare function found for symbol: " + symbol)
        
        # 拉取全量数据（从最早到今日）
        fetch_start = "19900101"
        fetch_end   = datetime.now().strftime("%Y%m%d")
        
        last_err = None
        df_raw = None
        for fn in fetch_targets:
            try:
                df_raw = fn(symbol=symbol, start_date=fetch_start, end_date=fetch_end)
                if df_raw is not None and not df_raw.empty:
                    break
            except TypeError:
                # 有些函数不支持 start_date/end_date 参数
                try:
                    df_raw = fn(symbol)
                    if df_raw is not None and not df_raw.empty:
                        break
                except Exception as e:
                    last_err = e
            except Exception as e:
                last_err = e
        
        if df_raw is None or df_raw.empty:
            if last_err:
                raise RuntimeError(f"AKShare fetch failed: {last_err}")
            return pd.DataFrame()
        
        # ---------- 标准化列名 ----------
        df = df_raw.copy()
        if not isinstance(df.index, pd.RangeIndex):
            df = df.reset_index()
        
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
            # 大小写不敏感兜底
            if target not in col_map:
                for col in df.columns:
                    if col.lower() in [c.lower() for c in keys]:
                        col_map[target] = col
                        break
        
        normalized = pd.DataFrame()
        # date
        if "date" in col_map:
            normalized["date"] = pd.to_datetime(df[col_map["date"]])
        else:
            normalized["date"] = pd.to_datetime(df.iloc[:, 0])
        
        # 数值列
        for key in ("open", "high", "low", "close", "volume", "amount", 
                    "amplitude", "pct_change", "change", "turnover_rate"):
            if key in col_map:
                normalized[key] = pd.to_numeric(df[col_map[key]], errors="coerce")
            else:
                normalized[key] = pd.NA
        
        normalized["symbol"] = symbol
        normalized = normalized.dropna(subset=["close"])
        normalized = normalized.sort_values("date").reset_index(drop=True)
        
        # ---------- 补充计算振幅、涨跌幅、涨跌额（如果原始数据缺失） ----------
        if not normalized.empty:
            # 检查是否需要自行计算
            need_amplitude = normalized["amplitude"].isna().all()
            need_change    = normalized["change"].isna().all()
            need_pct       = normalized["pct_change"].isna().all()
            
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
                        cur_low  = row["low"]
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


    def _save_kline_to_db(self, session, symbol: str, df: pd.DataFrame):
        """将 DataFrame 写入 SQLite（先删后插）"""
        try:
            # 删除该股票所有旧数据
            session.query(Kline).filter(Kline.symbol == symbol).delete(synchronize_session=False)
            
            # 插入新数据
            to_insert = []
            for _, row in df.iterrows():
                dt = pd.to_datetime(row['date']).to_pydatetime()
                k = Kline(
                    symbol=symbol,
                    date=dt,
                    open=float(row.get('open', 0.0) if pd.notna(row.get('open')) else 0.0),
                    high=float(row.get('high', 0.0) if pd.notna(row.get('high')) else 0.0),
                    low=float(row.get('low', 0.0) if pd.notna(row.get('low')) else 0.0),
                    close=float(row.get('close', 0.0) if pd.notna(row.get('close')) else 0.0),
                    volume=float(row.get('volume', 0.0) if pd.notna(row.get('volume')) else 0.0),
                    amount=float(row.get('amount', 0.0) if pd.notna(row.get('amount')) else 0.0),
                    amplitude=float(row.get('amplitude', 0.0) if pd.notna(row.get('amplitude')) else 0.0),
                    pct_change=float(row.get('pct_change', 0.0) if pd.notna(row.get('pct_change')) else 0.0),
                    change=float(row.get('change', 0.0) if pd.notna(row.get('change')) else 0.0),
                    turnover_rate=float(row.get('turnover_rate', 0.0) if pd.notna(row.get('turnover_rate')) else 0.0),
                )
                to_insert.append(k)
            
            if to_insert:
                session.add_all(to_insert)
            session.commit()
        
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to save Kline data to DB for {symbol}: {e}")
