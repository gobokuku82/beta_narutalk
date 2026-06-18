import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  children,
  ...props
}) => {
  // 상태별 스타일 정의
  const baseStyles = `
    inline-flex items-center justify-center font-medium rounded-lg
    transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
  `;

  // variant 별 스타일 (Default, Hover, Active, Disabled 포함)
  const variantStyles = {
    primary: `
      bg-accent text-white
      hover:bg-accent/90 hover:shadow-lg hover:scale-[1.02]
      active:bg-accent/80 active:scale-[0.98]
      disabled:bg-gray-300 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none
      focus:ring-accent
    `,
    secondary: `
      bg-gray-100 text-gray-700 border border-gray-300
      hover:bg-gray-200 hover:border-gray-400
      active:bg-gray-300
      disabled:bg-gray-50 disabled:text-gray-400 disabled:border-gray-200 disabled:cursor-not-allowed
      focus:ring-gray-400
    `,
    danger: `
      bg-danger text-white
      hover:bg-danger/90 hover:shadow-lg
      active:bg-danger/80
      disabled:bg-danger/30 disabled:cursor-not-allowed
      focus:ring-danger
    `,
    ghost: `
      bg-transparent text-gray-600
      hover:bg-gray-100 hover:text-gray-900
      active:bg-gray-200
      disabled:text-gray-300 disabled:cursor-not-allowed disabled:hover:bg-transparent
      focus:ring-gray-400
    `,
  };

  // 사이즈별 스타일
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-base gap-2',
    lg: 'px-6 py-3 text-lg gap-2.5',
  };

  // Loading 상태 스타일
  const loadingStyles = loading ? 'cursor-wait opacity-80' : '';

  return (
    <button
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${loadingStyles}
        ${className}
      `}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <Loader2 className={`animate-spin ${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'}`} />
      )}
      {children}
    </button>
  );
};

// 사용 예시를 위한 export
export default Button;