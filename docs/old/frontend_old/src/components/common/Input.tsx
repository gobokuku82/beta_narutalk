import React from 'react';
import { AlertCircle } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  fullWidth = false,
  className = '',
  ...props
}) => {
  const [isFocused, setIsFocused] = React.useState(false);
  const hasValue = props.value && String(props.value).length > 0;

  // 상태별 스타일 정의
  const getInputStyles = () => {
    let styles = `
      px-3 py-2 rounded-lg border transition-all duration-200
      placeholder:text-gray-400 text-gray-900
    `;

    if (error) {
      // Error 상태
      styles += `
        border-danger bg-danger/5
        focus:border-danger focus:ring-2 focus:ring-danger/20
      `;
    } else if (isFocused) {
      // Focused 상태
      styles += `
        border-accent bg-white
        ring-2 ring-accent/20
      `;
    } else if (hasValue) {
      // Filled 상태
      styles += `
        border-gray-300 bg-white
        hover:border-gray-400
      `;
    } else {
      // Empty (Default) 상태
      styles += `
        border-gray-200 bg-gray-50
        hover:border-gray-300 hover:bg-white
      `;
    }

    if (props.disabled) {
      styles += ` opacity-50 cursor-not-allowed bg-gray-100`;
    }

    return styles;
  };

  const containerClass = fullWidth ? 'w-full' : '';

  return (
    <div className={`${containerClass} ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {props.required && <span className="text-danger ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        <input
          className={getInputStyles()}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />

        {error && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-danger">
            <AlertCircle className="w-5 h-5" />
          </div>
        )}
      </div>

      {(error || helperText) && (
        <div className={`mt-1 text-sm ${error ? 'text-danger' : 'text-gray-500'}`}>
          {error || helperText}
        </div>
      )}
    </div>
  );
};

// 사용 예시를 위한 export
export default Input;