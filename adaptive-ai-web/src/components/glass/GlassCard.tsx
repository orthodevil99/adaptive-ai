import React from 'react';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  level?: 'surface' | 'elevated' | 'overlay' | 'user';
}

export const GlassCard: React.FC<GlassCardProps> = ({ level = 'surface', className = '', children, ...rest }) => {
  const cls =
    level === 'elevated'
      ? 'glass-elevated'
      : level === 'overlay'
        ? 'glass-overlay'
        : level === 'user'
          ? 'glass-user'
          : 'glass';
  return (
    <div className={`${cls} ${className}`} {...rest}>
      {children}
    </div>
  );
};
