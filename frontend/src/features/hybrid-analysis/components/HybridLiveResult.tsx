import { Zap, CheckCircle, XCircle } from 'lucide-react';
import { HybridLiveModeResult } from '../../../types/hybrid';

interface HybridLiveResultProps {
  result: HybridLiveModeResult;
  isKo: boolean;
}

export default function HybridLiveResult({ result, isKo }: HybridLiveResultProps) {
  if (!result.success) return null;

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Zap className="w-5 h-5 text-green-400" />
        {isKo ? '라이브 모드 결과' : 'Live Mode Results'}
      </h2>
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 p-4 bg-dark-800 rounded-lg">
          <div>
            <div className="text-sm text-dark-400">{isKo ? '타임스탬프' : 'Timestamp'}</div>
            <div className="text-sm font-mono text-white">
              {new Date(result.timestamp).toLocaleString('ko-KR')}
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '현재 가격' : 'Current Price'}</div>
            <div className="text-lg font-bold text-white">
              {result.current_price?.toFixed(2) || 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-400">{isKo ? '활성 전략 수' : 'Active Strategies'}</div>
            <div className="text-lg font-bold text-green-400">
              {result.strategies.filter(s => s.is_active).length} / {result.strategies.length}
            </div>
          </div>
        </div>
        
        <div className="space-y-3">
          {result.strategies.map((strategy) => (
            <div
              key={strategy.strategy}
              className={`p-4 rounded-lg border-2 ${
                strategy.is_active
                  ? 'bg-green-500/10 border-green-500/50'
                  : 'bg-dark-800 border-dark-600'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">{strategy.strategy}</h3>
                <div className="flex items-center gap-2">
                  {strategy.is_active ? (
                    <>
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <span className="text-green-400 font-semibold">{isKo ? '활성' : 'Active'}</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5 text-red-400" />
                      <span className="text-red-400 font-semibold">{isKo ? '비활성' : 'Inactive'}</span>
                    </>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                {strategy.strategy === 'SMA_ADX_Strong' && (
                  <>
                    <div>
                      <div className="text-dark-400">SMA20</div>
                      <div className="text-white font-mono">{strategy.conditions.sma20?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">SMA50</div>
                      <div className="text-white font-mono">{strategy.conditions.sma50?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">ADX</div>
                      <div className="text-white font-mono">{strategy.conditions.adx?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">SMA20 &gt; SMA50</div>
                      <div className={strategy.conditions.sma20_above_sma50 ? 'text-green-400' : 'text-red-400'}>
                        {strategy.conditions.sma20_above_sma50 ? '✓' : '✗'}
                      </div>
                    </div>
                    <div>
                      <div className="text-dark-400">ADX &gt; 25</div>
                      <div className={strategy.conditions.adx_above_25 ? 'text-green-400' : 'text-red-400'}>
                        {strategy.conditions.adx_above_25 ? '✓' : '✗'}
                      </div>
                    </div>
                  </>
                )}
                {strategy.strategy === 'MACD_RSI_Trend' && (
                  <>
                    <div>
                      <div className="text-dark-400">MACD Hist</div>
                      <div className="text-white font-mono">{strategy.conditions.macd_hist?.toFixed(4) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">RSI</div>
                      <div className="text-white font-mono">{strategy.conditions.rsi?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">Close</div>
                      <div className="text-white font-mono">{strategy.conditions.close?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">SMA200</div>
                      <div className="text-white font-mono">{strategy.conditions.sma200?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">MACD &gt; 0</div>
                      <div className={strategy.conditions.macd_positive ? 'text-green-400' : 'text-red-400'}>
                        {strategy.conditions.macd_positive ? '✓' : '✗'}
                      </div>
                    </div>
                    <div>
                      <div className="text-dark-400">RSI &gt; 55</div>
                      <div className={strategy.conditions.rsi_above_55 ? 'text-green-400' : 'text-red-400'}>
                        {strategy.conditions.rsi_above_55 ? '✓' : '✗'}
                      </div>
                    </div>
                    <div>
                      <div className="text-dark-400">Close &gt; SMA200</div>
                      <div className={strategy.conditions.close_above_sma200 ? 'text-green-400' : 'text-red-400'}>
                        {strategy.conditions.close_above_sma200 ? '✓' : '✗'}
                      </div>
                    </div>
                  </>
                )}
                {strategy.strategy === 'Pure_Trend' && (
                  <>
                    <div>
                      <div className="text-dark-400">Close</div>
                      <div className="text-white font-mono">{strategy.conditions.close?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">SMA200</div>
                      <div className="text-white font-mono">{strategy.conditions.sma200?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-dark-400">Close &gt; SMA200</div>
                      <div className={strategy.conditions.close_above_sma200 ? 'text-green-400' : 'text-red-400'}>
                        {strategy.conditions.close_above_sma200 ? '✓' : '✗'}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
