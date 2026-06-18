import React, { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

interface DateRangePickerProps {
  startDate: Date;
  endDate: Date;
  onDateChange: (start: Date, end: Date) => void;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onDateChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localStartDate, setLocalStartDate] = useState(startDate);
  const [localEndDate, setLocalEndDate] = useState(endDate);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectingEndDate, setSelectingEndDate] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 빠른 선택 옵션
  const quickSelections = [
    { label: '오늘', getValue: () => ({ start: new Date(), end: new Date() }) },
    {
      label: '최근 7일',
      getValue: () => {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 6);
        return { start, end };
      },
    },
    {
      label: '최근 30일',
      getValue: () => {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 29);
        return { start, end };
      },
    },
    {
      label: '이번 달',
      getValue: () => {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth(), 1);
        const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        return { start, end };
      },
    },
    {
      label: '지난 달',
      getValue: () => {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const end = new Date(now.getFullYear(), now.getMonth(), 0);
        return { start, end };
      },
    },
  ];

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).replace(/\. /g, '.').replace(/\.$/, '');
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days: (number | null)[] = [];

    // 빈 칸 채우기
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }

    // 날짜 채우기
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }

    return days;
  };

  const handleDateClick = (day: number) => {
    const selectedDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);

    if (!selectingEndDate) {
      setLocalStartDate(selectedDate);
      setLocalEndDate(selectedDate);
      setSelectingEndDate(true);
    } else {
      if (selectedDate < localStartDate) {
        setLocalStartDate(selectedDate);
      } else {
        setLocalEndDate(selectedDate);
      }
      setSelectingEndDate(false);
    }
  };

  const isDateInRange = (day: number) => {
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    return date >= localStartDate && date <= localEndDate;
  };

  const isStartDate = (day: number) => {
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    return date.toDateString() === localStartDate.toDateString();
  };

  const isEndDate = (day: number) => {
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    return date.toDateString() === localEndDate.toDateString();
  };

  const handleApply = () => {
    onDateChange(localStartDate, localEndDate);
    setIsOpen(false);
  };

  const handleQuickSelection = (getValue: () => { start: Date; end: Date }) => {
    const { start, end } = getValue();
    setLocalStartDate(start);
    setLocalEndDate(end);
    setCurrentMonth(new Date(start));
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm"
      >
        <Calendar className="w-4 h-4 text-gray-500" />
        <span className="text-gray-700">
          {formatDate(startDate)} - {formatDate(endDate)}
        </span>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-[480px] bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="flex">
            {/* 빠른 선택 영역 */}
            <div className="w-32 border-r border-gray-200 p-3">
              <p className="text-xs font-medium text-gray-500 mb-2">빠른 선택</p>
              <div className="space-y-1">
                {quickSelections.map((selection) => (
                  <button
                    key={selection.label}
                    onClick={() => handleQuickSelection(selection.getValue)}
                    className="w-full text-left px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded transition-colors"
                  >
                    {selection.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 캘린더 영역 */}
            <div className="flex-1 p-4">
              {/* 월 네비게이션 */}
              <div className="flex items-center justify-between mb-3">
                <button
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-medium text-sm">
                  {currentMonth.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long' })}
                </span>
                <button
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* 요일 헤더 */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {['일', '월', '화', '수', '목', '금', '토'].map((day) => (
                  <div key={day} className="text-center text-xs font-medium text-gray-500">
                    {day}
                  </div>
                ))}
              </div>

              {/* 날짜 그리드 */}
              <div className="grid grid-cols-7 gap-1">
                {getDaysInMonth(currentMonth).map((day, index) => (
                  <div key={index}>
                    {day ? (
                      <button
                        onClick={() => handleDateClick(day)}
                        className={`w-full h-8 text-sm rounded transition-colors ${
                          isStartDate(day) || isEndDate(day)
                            ? 'bg-blue-500 text-white hover:bg-blue-600'
                            : isDateInRange(day)
                            ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        {day}
                      </button>
                    ) : (
                      <div className="w-full h-8" />
                    )}
                  </div>
                ))}
              </div>

              {/* 선택된 날짜 표시 */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-gray-500">시작:</span>
                    <span className="ml-2 font-medium">{formatDate(localStartDate)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">종료:</span>
                    <span className="ml-2 font-medium">{formatDate(localEndDate)}</span>
                  </div>
                </div>
              </div>

              {/* 액션 버튼 */}
              <div className="flex justify-end gap-2 mt-3">
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleApply}
                  className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  적용
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;