import React from 'react';
import { Check } from 'lucide-react';

interface MessageRendererProps {
  content: string;
}

export const MessageRenderer: React.FC<MessageRendererProps> = ({ content }) => {
  // 간단한 마크다운 파서
  const parseMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let inTable = false;
    let tableData: string[][] = [];
    let inCodeBlock = false;
    let codeContent: string[] = [];

    lines.forEach((line, index) => {
      // 코드 블록
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          elements.push(
            <pre key={index} className="bg-gray-100 p-3 rounded-lg overflow-x-auto">
              <code className="text-sm">{codeContent.join('\n')}</code>
            </pre>
          );
          codeContent = [];
        }
        inCodeBlock = !inCodeBlock;
        return;
      }

      if (inCodeBlock) {
        codeContent.push(line);
        return;
      }

      // 테이블
      if (line.includes('|') && line.trim().startsWith('|')) {
        if (!inTable) {
          inTable = true;
          tableData = [];
        }

        if (line.includes('---')) return; // 구분선 무시

        const cells = line.split('|').filter(cell => cell.trim());
        tableData.push(cells);

        // 다음 줄이 테이블이 아니면 렌더링
        if (index === lines.length - 1 || !lines[index + 1].includes('|')) {
          elements.push(renderTable(tableData, index));
          inTable = false;
          tableData = [];
        }
        return;
      }

      // 헤딩
      if (line.startsWith('###')) {
        const text = line.replace(/###\s*/, '');
        const { icon, formattedText } = processText(text);
        elements.push(
          <h3 key={index} className="text-lg font-semibold text-gray-900 mt-4 mb-2 flex items-center gap-2">
            {icon}
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </h3>
        );
      } else if (line.startsWith('##')) {
        const text = line.replace(/##\s*/, '');
        const { icon, formattedText } = processText(text);
        elements.push(
          <h2 key={index} className="text-xl font-bold text-gray-900 mt-4 mb-3 flex items-center gap-2">
            {icon}
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </h2>
        );
      } else if (line.startsWith('####')) {
        const text = line.replace(/####\s*/, '');
        elements.push(
          <h4 key={index} className="text-base font-semibold text-gray-800 mt-3 mb-2">
            {processText(text).formattedText}
          </h4>
        );
      }
      // 인용문
      else if (line.startsWith('>')) {
        const text = line.replace(/>\s*/, '');
        elements.push(
          <blockquote key={index} className="border-l-4 border-blue-500 pl-4 my-2 text-gray-700 italic bg-blue-50 py-2 pr-3 rounded-r">
            {processText(text).formattedText}
          </blockquote>
        );
      }
      // 체크리스트
      else if (line.includes('- [ ]') || line.includes('- [x]')) {
        const isChecked = line.includes('- [x]');
        const text = line.replace(/- \[(x| )\]\s*/, '');
        elements.push(
          <div key={index} className="flex items-center gap-2 my-1">
            <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
              isChecked ? 'bg-green-500 border-green-500' : 'border-gray-300'
            }`}>
              {isChecked && <Check className="w-3 h-3 text-white" />}
            </div>
            <span className={isChecked ? 'line-through text-gray-500' : 'text-gray-700'}>
              {processText(text).formattedText}
            </span>
          </div>
        );
      }
      // 번호 리스트
      else if (/^\d+\.\s/.test(line)) {
        const text = line.replace(/^\d+\.\s*/, '');
        const { formattedText } = processText(text);
        elements.push(
          <div key={index} className="flex gap-3 my-2">
            <span className="font-semibold text-blue-600">{line.match(/^\d+/)?.[0]}.</span>
            <span className="flex-1" dangerouslySetInnerHTML={{ __html: formattedText }} />
          </div>
        );
      }
      // 불릿 리스트
      else if (line.startsWith('-') || line.startsWith('•')) {
        const text = line.replace(/^[-•]\s*/, '');
        const { formattedText } = processText(text);
        elements.push(
          <div key={index} className="flex gap-2 my-1">
            <span className="text-blue-500">•</span>
            <span className="flex-1" dangerouslySetInnerHTML={{ __html: formattedText }} />
          </div>
        );
      }
      // 구분선
      else if (line.startsWith('---')) {
        elements.push(<hr key={index} className="my-4 border-gray-200" />);
      }
      // 일반 텍스트
      else if (line.trim()) {
        const { formattedText } = processText(line);
        elements.push(
          <p key={index} className="text-gray-700 my-1" dangerouslySetInnerHTML={{ __html: formattedText }} />
        );
      }
    });

    return elements;
  };

  // 텍스트 처리 (볼드, 이탤릭, 코드, 이모지, 색상 등)
  const processText = (text: string) => {
    let formattedText = text;
    let icon = null;

    // 이모지 아이콘 추출
    const emojiMatch = text.match(/^(📊|📈|💡|🎯|🎨|💰|✅|🚨|⚠️|ℹ️|🔴|🟢|🟡)/);
    if (emojiMatch) {
      icon = <span className="text-xl">{emojiMatch[1]}</span>;
      formattedText = formattedText.replace(emojiMatch[1], '').trim();
    }

    // 볼드 처리
    formattedText = formattedText.replace(
      /\*\*([^*]+)\*\*/g,
      '<strong class="font-bold text-gray-900">$1</strong>'
    );

    // 이탤릭 처리
    formattedText = formattedText.replace(
      /\*([^*]+)\*/g,
      '<em class="italic">$1</em>'
    );

    // 인라인 코드 처리
    formattedText = formattedText.replace(
      /`([^`]+)`/g,
      '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>'
    );

    // 색상 표시 처리
    formattedText = formattedText.replace(/🟢/g, '<span class="text-green-500">●</span>');
    formattedText = formattedText.replace(/🔴/g, '<span class="text-red-500">●</span>');
    formattedText = formattedText.replace(/🟡/g, '<span class="text-yellow-500">●</span>');

    // 퍼센트 강조
    formattedText = formattedText.replace(
      /(\+?\-?\d+(?:\.\d+)?%)/g,
      '<span class="font-semibold text-blue-600">$1</span>'
    );

    // 금액 강조 (₩ 포함)
    formattedText = formattedText.replace(
      /(₩[\d,]+(?:K|M)?)/g,
      '<span class="font-semibold text-green-600">$1</span>'
    );

    return { icon, formattedText };
  };

  // 테이블 렌더링
  const renderTable = (data: string[][], key: number) => {
    if (data.length === 0) return null;

    const headers = data[0];
    const rows = data.slice(1);

    return (
      <div key={key} className="overflow-x-auto my-4">
        <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
          <thead className="bg-gray-50">
            <tr>
              {headers.map((header, i) => (
                <th key={i} className="px-4 py-2 text-left text-sm font-semibold text-gray-700 border-b border-gray-200">
                  {processText(header.trim()).formattedText}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50 transition-colors">
                {row.map((cell, j) => {
                  const cellContent = cell.trim();
                  const { formattedText } = processText(cellContent);

                  // 상태 셀 특별 처리
                  let bgColor = '';
                  if (cellContent.includes('우수') || cellContent.includes('최우수')) {
                    bgColor = 'bg-green-50';
                  } else if (cellContent.includes('개선필요') || cellContent.includes('위험')) {
                    bgColor = 'bg-red-50';
                  } else if (cellContent.includes('보통') || cellContent.includes('주의')) {
                    bgColor = 'bg-yellow-50';
                  }

                  return (
                    <td
                      key={j}
                      className={`px-4 py-2 text-sm text-gray-700 border-b border-gray-100 ${bgColor}`}
                      dangerouslySetInnerHTML={{ __html: formattedText }}
                    />
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="prose-sm max-w-none">
      {parseMarkdown(content)}
    </div>
  );
};