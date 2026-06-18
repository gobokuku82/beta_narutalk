/**
 * DataLoadError — 데이터 로드 실패 공통 화면.
 *
 * Status: complete — 7개 데이터 페이지의 에러 분기를 공통화.
 * 개발용 문구(서버 주소 등) 노출 없이 사용자용 메시지만 표시.
 */
import type { LucideIcon } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface DataLoadErrorProps {
  title: string;
  icon?: LucideIcon;
}

export function DataLoadError({ title, icon }: DataLoadErrorProps) {
  return (
    <div className="p-6">
      <PageHeader title={title} icon={icon} />
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-destructive">
            데이터를 불러오지 못했어요
          </CardTitle>
          <CardDescription>잠시 후 다시 시도해 주세요.</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
