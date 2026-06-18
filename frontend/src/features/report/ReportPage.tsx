/**
 * ReportPage — 통합 성과 리포트.
 *
 * 2026-05-28: 구 mock-API(data/mock) 단절로 stub 전환. 리포트 생성은 추후
 * pipeline 산출 + report_writer tool 기반으로 재구성 예정 (MVP+).
 */
import { FileText } from 'lucide-react';

import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent } from '@/components/ui/card';

export function ReportPage() {
  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6">
      <PageHeader title="리포트" description="통합 성과 리포트" icon={FileText} badge="준비 중" />
      <Card>
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          통합 리포트는 pipeline 산출 + 리포트 생성 tool 기반으로 재구성 예정입니다 (MVP+).
          <br />
          현재 분석은 좌측 <b>대시보드1 · 채널 · 트렌드 · 소재 · 비용</b> 페이지에서 확인하세요.
        </CardContent>
      </Card>
    </div>
  );
}
