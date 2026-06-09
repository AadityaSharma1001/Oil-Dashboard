import React, { memo } from 'react';

/**
 * Reusable Card wrapper with hover shadow transition.
 * Accepts optional `source` prop ('live' | 'mock' | 'loading') for data provenance.
 */
const Card = memo(function Card({
  title,
  badge,
  badgeVariant = 'default',
  footer,
  className = '',
  source,
  children,
}) {
  const badgeClasses = {
    default: 'bg-slate-100 text-slate-500',
    amber: 'bg-amber-50 text-amber-700',
    blue: 'bg-blue-50 text-blue-900',
    green: 'bg-emerald-50 text-emerald-700',
    red: 'bg-red-50 text-red-700',
  };

  const sourceColor = source === 'live' ? 'bg-emerald-400' : source === 'mock' ? 'bg-amber-400' : source === 'degraded' ? 'bg-yellow-300' : null;

  return (
    <div className={`bg-white border border-slate-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden ${className}`}>
      {title && (
        <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-slate-100">
          <div className="flex items-center gap-1.5">
            {sourceColor && (
              <span className={`w-[6px] h-[6px] rounded-full ${sourceColor}`} title={`Data: ${source}`} />
            )}
            <h3 className="text-[12.5px] font-semibold text-slate-700">{title}</h3>
          </div>
          {badge && (
            <span className={`text-[10px] font-medium px-2 py-0.5 rounded ${badgeClasses[badgeVariant] || badgeClasses.default}`}>
              {badge}
            </span>
          )}
        </div>
      )}
      <div className="p-3.5">{children}</div>
      {footer && (
        <div className="px-3.5 py-2.5 border-t border-slate-100">{footer}</div>
      )}
    </div>
  );
});

export default Card;

