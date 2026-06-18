import React from 'react';

export const ColorTest: React.FC = () => {
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold mb-6">색상 테스트 페이지</h1>

      <div className="grid grid-cols-4 gap-4">
        <div className="space-y-2">
          <h3 className="font-semibold">Success 계열</h3>
          <div className="p-4 bg-success text-white">bg-success</div>
          <div className="p-4 bg-success-bg text-success-dark">bg-success-bg / text-success-dark</div>
          <div className="p-4 border-2 border-success">border-success</div>
          <div className="p-4 text-success">text-success</div>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">Warning 계열</h3>
          <div className="p-4 bg-warning text-white">bg-warning</div>
          <div className="p-4 bg-warning-bg text-warning-dark">bg-warning-bg / text-warning-dark</div>
          <div className="p-4 border-2 border-warning">border-warning</div>
          <div className="p-4 text-warning">text-warning</div>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">Danger 계열</h3>
          <div className="p-4 bg-danger text-white">bg-danger</div>
          <div className="p-4 bg-danger-bg text-danger-dark">bg-danger-bg / text-danger-dark</div>
          <div className="p-4 border-2 border-danger">border-danger</div>
          <div className="p-4 text-danger">text-danger</div>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">Accent/Info 계열</h3>
          <div className="p-4 bg-accent text-white">bg-accent</div>
          <div className="p-4 bg-info-bg text-accent">bg-info-bg / text-accent</div>
          <div className="p-4 border-2 border-accent">border-accent</div>
          <div className="p-4 text-info">text-info</div>
        </div>
      </div>

      <div className="mt-8">
        <h3 className="font-semibold mb-4">채널 색상</h3>
        <div className="flex gap-4">
          <div className="p-4 bg-naver text-white">네이버</div>
          <div className="p-4 bg-kakao text-black">카카오</div>
          <div className="p-4 bg-meta text-white">메타</div>
          <div className="p-4 bg-google text-white">구글</div>
        </div>
      </div>

      <div className="mt-8 p-4 bg-gray-100 rounded">
        <h3 className="font-semibold mb-2">CSS 변수 확인</h3>
        <p className="text-sm text-gray-600">
          개발자 도구 &gt; Elements &gt; :root 에서 CSS 변수 정의 확인 가능
        </p>
        <ul className="text-sm mt-2 space-y-1">
          <li>--color-success: #22c55e</li>
          <li>--color-warning: #f97316</li>
          <li>--color-danger: #ef4444</li>
          <li>--accent: #4a90d9</li>
        </ul>
      </div>
    </div>
  );
};