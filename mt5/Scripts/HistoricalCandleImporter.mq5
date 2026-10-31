//+------------------------------------------------------------------+
//| XAUUSD AI Command Centre - Historical Candle Importer             |
//| One-shot, read-only MT5 script. Imports closed bars into cloud DB.|
//+------------------------------------------------------------------+
#property strict
#property version "1.00"
#property script_show_inputs
#property description "Imports historical OHLC candles from the current MT5 broker to the research database."

input string IngestUrl = "https://xauusd-ai-command-centre-api.onrender.com";
input string IngestKey = "";                 // Set locally; never share this key
input string CanonicalSymbol = "XAUUSD";     // XAUUSD or EURUSD
input ENUM_TIMEFRAMES ImportTimeframe = PERIOD_M1;
input int BarsToImport = 10000;               // Closed bars only; terminal history must be available
input int BatchSize = 500;                    // API accepts up to 5000 per batch
input string SourceTag = "pepperstone_mt5_history";

string TimeframeName(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_M1: return "M1";
      case PERIOD_M2: return "M2";
      case PERIOD_M3: return "M3";
      case PERIOD_M4: return "M4";
      case PERIOD_M5: return "M5";
      case PERIOD_M6: return "M6";
      case PERIOD_M10: return "M10";
      case PERIOD_M12: return "M12";
      case PERIOD_M15: return "M15";
      case PERIOD_M20: return "M20";
      case PERIOD_M30: return "M30";
      case PERIOD_H1: return "H1";
      case PERIOD_H2: return "H2";
      case PERIOD_H3: return "H3";
      case PERIOD_H4: return "H4";
      case PERIOD_H6: return "H6";
      case PERIOD_H8: return "H8";
      case PERIOD_H12: return "H12";
      case PERIOD_D1: return "D1";
      case PERIOD_W1: return "W1";
      case PERIOD_MN1: return "MN1";
   }
   return EnumToString(tf);
}

string IsoUtc(datetime broker_time)
{
   int offset = (int)(TimeTradeServer() - TimeGMT());
   datetime utc_time = broker_time - offset;
   MqlDateTime dt;
   TimeToStruct(utc_time, dt);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02dZ",
                       dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
}

bool PostBatch(const string body, int &http_status)
{
   string url = IngestUrl + "/api/v1/market-data/candles/batch";
   string headers = "Content-Type: application/json\r\nX-Ingest-Key: " + IngestKey + "\r\n";
   char data[], result[];
   string response_headers;
   int copied = StringToCharArray(body, data, 0, WHOLE_ARRAY, CP_UTF8);
   if(copied > 0) ArrayResize(data, copied - 1);
   ResetLastError();
   http_status = WebRequest("POST", url, headers, 20000, data, result, response_headers);
   if(http_status >= 200 && http_status < 300)
   {
      Print("Historical importer: ", CharArrayToString(result));
      return true;
   }
   PrintFormat("Historical importer POST failed. HTTP=%d, MT5 error=%d, response=%s",
               http_status, GetLastError(), CharArrayToString(result));
   return false;
}

void OnStart()
{
   if(IngestKey == "")
   {
      Alert("Set IngestKey in the script inputs first.");
      return;
   }
   if(CanonicalSymbol != "XAUUSD" && CanonicalSymbol != "EURUSD")
   {
      Alert("CanonicalSymbol must be XAUUSD or EURUSD.");
      return;
   }
   if(BarsToImport < 2 || BatchSize < 1 || BatchSize > 5000)
   {
      Alert("BarsToImport must be >= 2 and BatchSize must be 1..5000.");
      return;
   }

   string symbol = _Symbol;
   if(!SymbolSelect(symbol, true))
   {
      Alert("Could not select chart symbol: ", symbol);
      return;
   }

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   ResetLastError();
   int copied = CopyRates(symbol, ImportTimeframe, 1, BarsToImport, rates);
   if(copied < 2)
   {
      PrintFormat("Historical importer: only %d bars available. MT5 error=%d. Load more chart history and retry.",
                  copied, GetLastError());
      Alert("Not enough historical bars loaded. Open the chart, press Home to load history, then retry.");
      return;
   }

   string tf = TimeframeName(ImportTimeframe);
   int stored = 0;
   int failed = 0;
   for(int start = 0; start < copied; start += BatchSize)
   {
      int count = MathMin(BatchSize, copied - start);
      string body = "{\"candles\":[";
      for(int j = 0; j < count; j++)
      {
         int k = start + j;
         if(j > 0) body += ",";
         body += StringFormat(
            "{\"symbol\":\"%s\",\"timeframe\":\"%s\",\"open_time\":\"%s\",\"open\":%s,\"high\":%s,\"low\":%s,\"close\":%s,\"volume\":%I64d,\"source\":\"%s\"}",
            CanonicalSymbol, tf, IsoUtc(rates[k].time),
            DoubleToString(rates[k].open, _Digits),
            DoubleToString(rates[k].high, _Digits),
            DoubleToString(rates[k].low, _Digits),
            DoubleToString(rates[k].close, _Digits),
            rates[k].tick_volume, SourceTag
         );
      }
      body += "]}";
      int http_status = 0;
      if(PostBatch(body, http_status))
         stored += count;
      else
      {
         failed += count;
         PrintFormat("Historical importer stopped at batch starting bar %d. Fix the error and rerun; duplicate bars are safely upserted.", start);
         break;
      }
      PrintFormat("Historical import progress: %d / %d bars", stored, copied);
   }

   PrintFormat("Historical import finished. Symbol=%s, timeframe=%s, bars copied=%d, bars stored=%d, failed=%d",
               CanonicalSymbol, tf, copied, stored, failed);
   Alert(StringFormat("Historical import: %d bars stored, %d failed. Check Experts tab and dashboard data summary.",
                      stored, failed));
}
