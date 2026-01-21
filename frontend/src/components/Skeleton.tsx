// Skeleton UI Components for Loading States
import React from 'react';

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => (
  <div className={`animate-pulse bg-dark-700 rounded ${className}`} />
);

export const SkeletonCard: React.FC = () => (
  <div className="card p-6 space-y-4">
    <div className="flex items-center justify-between">
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-4 w-20" />
    </div>
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
    <div className="grid grid-cols-2 gap-4 mt-4">
      <Skeleton className="h-20" />
      <Skeleton className="h-20" />
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number; cols?: number }> = ({ 
  rows = 5, 
  cols = 4 
}) => (
  <div className="card p-6">
    <Skeleton className="h-6 w-40 mb-4" />
    <div className="space-y-3">
      {/* Header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={`header-${i}`} className="h-4" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={`row-${rowIdx}`} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {Array.from({ length: cols }).map((_, colIdx) => (
            <Skeleton key={`cell-${rowIdx}-${colIdx}`} className="h-8" />
          ))}
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonChart: React.FC = () => (
  <div className="card p-6">
    <Skeleton className="h-6 w-48 mb-4" />
    <Skeleton className="h-64 w-full" />
    <div className="flex justify-center gap-4 mt-4">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-4 w-20" />
      <Skeleton className="h-4 w-20" />
    </div>
  </div>
);

export const SkeletonStats: React.FC = () => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    {Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="card p-4">
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-32" />
      </div>
    ))}
  </div>
);

export const SkeletonAnalysis: React.FC = () => (
  <div className="space-y-6">
    {/* Stats Grid */}
    <SkeletonStats />
    
    {/* Main Content Cards */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <SkeletonCard />
      <SkeletonCard />
    </div>
    
    {/* Chart */}
    <SkeletonChart />
    
    {/* Table */}
    <SkeletonTable rows={8} cols={5} />
  </div>
);
