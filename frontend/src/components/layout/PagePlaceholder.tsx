/**
 * PagePlaceholder — Sprint 1 placeholder. 페이지가 라우트 OK 임을 확인용.
 * 2026-06-01: mockCsv prop 폐기 (구 /api/mock layer 정리). 실제 데이터 = pipeline 산출 (data/{client}/computed/).
 */
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface PagePlaceholderProps {
  title: string;
  description: string;
  sprintTarget: string; // 예: "Sprint 2"
}

export function PagePlaceholder({
  title,
  description,
  sprintTarget,
}: PagePlaceholderProps) {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <h1 className="text-heading-md font-display">{title}</h1>
        <Badge variant="secondary">{sprintTarget}</Badge>
      </div>
      <p className="text-muted-foreground">{description}</p>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Sprint 1 placeholder</CardTitle>
          <CardDescription>
            라우터가 이 페이지에 도달했습니다. 실제 콘텐츠는 {sprintTarget} 에서 채워집니다.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
