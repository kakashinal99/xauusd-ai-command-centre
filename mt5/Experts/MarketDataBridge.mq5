//+------------------------------------------------------------------+
//| Pepperstone MT5 Market Data Bridge                               |
//| Read-only: sends ticks and closed M1 candles to the AI backend.  |
//| No trade functions are used.                                      |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Read-only market data bridge for the XAUUSD AI Command Centre"

input string IngestUrl = "https://xauusd-ai-command-centre-api.onrender.com";
input string IngestKey = "";                 // Set locally in EA inputs; never share it
input string CanonicalSymbol = "XAUUSD";     // Backend symbol: XAUUSD or EURUSD
input string SourceTag = "pepperstone_mt5";
input int    FlushIntervalSeconds = 2;
input int    MaxQueuedTicks = 250;

string g_ticks[];
datetime g_last_m1_open = 0;
int g_sent_ticks = 0;
int g_sent_candles = 0;
int g_failed_posts = 0;

string IsoUtc(datetime broker_time)
{
   int offset = (int)(TimeTradeServer() - TimeGMT());
   datetime utc_time = broker_time - offset;
   MqlDateTime dt;
   TimeToStruct(utc_time, dt);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02dZ",
                       dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
}

bool PostJson(string path, string body)
{
   if(StringLen(IngestKey) == 0)
   {
      Print("MarketDataBridge: set IngestKey in EA inputs.");
      return false;
   }

   string url = IngestUrl + path;
   string headers = "Content-Type: application/json\r\nX-Ingest-Key: " + IngestKey + "\r\n";
   char data[];
   char result[];
   string result_headers;
   int copied = StringToCharArray(body, data, 0, WHOLE_ARRAY, CP_UTF8);
   if(copied > 0)
      ArrayResize(data, copied - 1); // remove terminating null byte

   ResetLastError();
   int status = WebRequest("POST", url, headers, 7000, data, result, result_headers);
   if(status >= 200 && status < 300)
      return true;

   PrintFormat("MarketDataBridge: POST %s failed. HTTP=%d, MT5 error=%d, response=%s",
               path, status, GetLastError(), CharArrayToString(result));
   return false;
}

void QueueTick(const MqlTick &tick)
{
   if(tick.time <= 0 || tick.bid <= 0 || tick.ask <= 0 || tick.ask < tick.bid)
      return;

   if(ArraySize(g_ticks) >= MaxQueuedTicks)
   {
      // Keep the newest market observations; discard the oldest queued item.
      for(int i=1; i<ArraySize(g_ticks); i++)
         g_ticks[i-1] = g_ticks[i];
      ArrayResize(g_ticks, ArraySize(g_ticks)-1);
   }

   string item = StringFormat(
      "{\"symbol\":\"%s\",\"event_time\":\"%s\",\"price\":%s,\"bid\":%s,\"ask\":%s,\"source\":\"%s\"}",
      CanonicalSymbol, IsoUtc(tick.time),
      DoubleToString(tick.last > 0 ? tick.last : (tick.bid + tick.ask) / 2.0, _Digits),
      DoubleToString(tick.bid, _Digits), DoubleToString(tick.ask, _Digits), SourceTag
   );
   int n = ArraySize(g_ticks);
   ArrayResize(g_ticks, n+1);
   g_ticks[n] = item;
}

void FlushTicks()
{
   int count = ArraySize(g_ticks);
   if(count == 0)
      return;

   string body = "{\"ticks\":[";
   for(int i=0; i<count; i++)
   {
      if(i > 0) body += ",";
      body += g_ticks[i];
   }
   body += "]}";

   if(PostJson("/api/v1/market-data/ticks/batch", body))
   {
      g_sent_ticks += count;
      ArrayResize(g_ticks, 0);
   }
   else
      g_failed_posts++;
}

void SendClosedM1Candle()
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_M1, 1, 1, rates) != 1)
      return;

   if(rates[0].time <= g_last_m1_open)
      return;

   string item = StringFormat(
      "{\"symbol\":\"%s\",\"timeframe\":\"M1\",\"open_time\":\"%s\",\"open\":%s,\"high\":%s,\"low\":%s,\"close\":%s,\"volume\":%I64d,\"source\":\"%s\"}",
      CanonicalSymbol, IsoUtc(rates[0].time),
      DoubleToString(rates[0].open, _Digits),
      DoubleToString(rates[0].high, _Digits),
      DoubleToString(rates[0].low, _Digits),
      DoubleToString(rates[0].close, _Digits),
      rates[0].tick_volume, SourceTag
   );
   string body = "{\"candles\":[" + item + "]}";
   if(PostJson("/api/v1/market-data/candles/batch", body))
   {
      g_last_m1_open = rates[0].time;
      g_sent_candles++;
   }
   else
      g_failed_posts++;
}

int OnInit()
{
   if(CanonicalSymbol != "XAUUSD" && CanonicalSymbol != "EURUSD")
   {
      Print("MarketDataBridge: CanonicalSymbol must be XAUUSD or EURUSD.");
      return INIT_PARAMETERS_INCORRECT;
   }
   if(FlushIntervalSeconds < 1 || MaxQueuedTicks < 10)
      return INIT_PARAMETERS_INCORRECT;

   ArrayResize(g_ticks, 0);
   EventSetTimer(FlushIntervalSeconds);
   PrintFormat("MarketDataBridge started. Chart=%s, backend symbol=%s, source=%s",
               _Symbol, CanonicalSymbol, SourceTag);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   FlushTicks();
   Comment("");
}

void OnTick()
{
   MqlTick tick;
   if(SymbolInfoTick(_Symbol, tick))
      QueueTick(tick);
}

void OnTimer()
{
   FlushTicks();
   SendClosedM1Candle();
   Comment("Market Data Bridge (READ ONLY)\n",
           "Chart: ", _Symbol, " | Backend: ", CanonicalSymbol, "\n",
           "Ticks sent: ", g_sent_ticks, " | M1 candles sent: ", g_sent_candles,
           " | Failed posts: ", g_failed_posts);
}
