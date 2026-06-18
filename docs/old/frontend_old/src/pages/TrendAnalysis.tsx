import React, { useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../app/store';
import {
  fetchTrendData,
  toggleKeyword,
  toggleCategory,
  clearSelections
} from '../features/trend/trendSlice';
import { EmptyState, LoadingState } from '../components/common';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const TrendAnalysis: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const currentClient = useSelector((state: RootState) => state.client.selectedClient);
  const { data, selectedKeywords, selectedCategories, isLoading, error } = useSelector(
    (state: RootState) => state.trend
  );

  useEffect(() => {
    if (currentClient) {
      dispatch(fetchTrendData(currentClient));
    }
  }, [currentClient, dispatch]);

  // 키워드 차트 데이터 준비
  const keywordChartData = useMemo(() => {
    if (!data.keywords.length) return [];

    const filteredKeywords = selectedKeywords.length
      ? data.keywords.filter(k => selectedKeywords.includes(k.keyword))
      : data.keywords.slice(0, 2); // 기본값: 처음 2개

    if (!filteredKeywords.length) return [];

    const dates = filteredKeywords[0].dates;
    return dates.map((date, index) => {
      const dataPoint: any = { date: date.slice(5) }; // MM-DD 형식
      filteredKeywords.forEach(keyword => {
        dataPoint[keyword.keyword] = keyword.values[index];
      });
      return dataPoint;
    });
  }, [data.keywords, selectedKeywords]);

  // 쇼핑 카테고리 차트 데이터 준비
  const categoryChartData = useMemo(() => {
    if (!data.shoppingCategories.length) return [];

    const filteredCategories = selectedCategories.length
      ? data.shoppingCategories.filter(c => selectedCategories.includes(c.category))
      : data.shoppingCategories.slice(0, 2); // 기본값: 처음 2개

    if (!filteredCategories.length) return [];

    const dates = filteredCategories[0].dates;
    return dates.map((date, index) => {
      const dataPoint: any = { date: date.slice(5) }; // MM-DD 형식
      filteredCategories.forEach(category => {
        dataPoint[category.category] = category.clicks[index];
      });
      return dataPoint;
    });
  }, [data.shoppingCategories, selectedCategories]);

  // 감성 분석 파이 차트 데이터
  const sentimentChartData = [
    { name: '긍정', value: data.sentimentAnalysis.positive, color: '#10B981' },
    { name: '부정', value: data.sentimentAnalysis.negative, color: '#EF4444' },
    { name: '중립', value: data.sentimentAnalysis.neutral, color: '#6B7280' }
  ];

  const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  if (isLoading) {
    return <LoadingState message="트렌드 데이터를 불러오는 중..." />;
  }

  if (error) {
    return (
      <EmptyState
        title="데이터를 불러올 수 없습니다"
        description={error}
        actionText="다시 시도"
        onAction={() => currentClient && dispatch(fetchTrendData(currentClient))}
      />
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">트렌드 분석</h1>
          <p className="text-sm text-gray-500 mt-1">
            시장 트렌드와 소비자 반응을 실시간으로 모니터링합니다
          </p>
        </div>
        <button
          onClick={() => dispatch(clearSelections())}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          선택 초기화
        </button>
      </div>

      {/* 키워드 검색량 추이 섹션 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">키워드 검색량 추이</h2>

          {/* 키워드 선택 버튼 */}
          <div className="flex flex-wrap gap-2 mb-4">
            {data.keywords.map((keyword) => (
              <button
                key={keyword.keyword}
                onClick={() => dispatch(toggleKeyword(keyword.keyword))}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  selectedKeywords.includes(keyword.keyword)
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {keyword.keyword}
              </button>
            ))}
            {selectedKeywords.length >= 5 && (
              <span className="text-xs text-gray-500 self-center ml-2">
                최대 5개까지 선택 가능
              </span>
            )}
          </div>

          {keywordChartData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={keywordChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={12} />
                  <YAxis stroke="#6B7280" fontSize={12} />
                  <Tooltip />
                  <Legend />
                  {(selectedKeywords.length ? selectedKeywords : data.keywords.slice(0, 2).map(k => k.keyword))
                    .map((keyword, index) => (
                      <Line
                        key={keyword}
                        type="monotone"
                        dataKey={keyword}
                        stroke={CHART_COLORS[index % CHART_COLORS.length]}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                </LineChart>
              </ResponsiveContainer>
              <p className="text-xs text-gray-500 mt-2 text-center">
                * 수치는 0~100 기준의 상대값입니다 (Naver DataLab 기준)
              </p>
            </>
          ) : (
            <EmptyState
              title="키워드 데이터가 없습니다"
              description="검색량 추이를 확인할 키워드가 없습니다."
            />
          )}
        </div>
      </div>

      {/* 쇼핑 카테고리 트렌드 섹션 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">쇼핑 카테고리 트렌드</h2>

          {/* 카테고리 선택 버튼 */}
          <div className="flex flex-wrap gap-2 mb-4">
            {data.shoppingCategories.map((category) => (
              <button
                key={category.category}
                onClick={() => dispatch(toggleCategory(category.category))}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  selectedCategories.includes(category.category)
                    ? 'bg-green-100 text-green-700 border-2 border-green-300'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category.category}
              </button>
            ))}
          </div>

          {categoryChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={categoryChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="date" stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip />
                <Legend />
                {(selectedCategories.length ? selectedCategories : data.shoppingCategories.slice(0, 2).map(c => c.category))
                  .map((category, index) => (
                    <Line
                      key={category}
                      type="monotone"
                      dataKey={category}
                      stroke={CHART_COLORS[index % CHART_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState
              title="카테고리 데이터가 없습니다"
              description="클릭 트렌드를 확인할 카테고리가 없습니다."
            />
          )}
        </div>
      </div>

      {/* 블로그·뉴스 감성 분석 섹션 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">블로그·뉴스 감성 분석</h2>

          {data.sentimentAnalysis.samples.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 파이 차트 */}
              <div className="flex flex-col items-center">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={sentimentChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name} ${entry.value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {sentimentChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* 최신 수집 텍스트 카드 리스트 */}
              <div className="lg:col-span-2 space-y-3">
                <h3 className="text-sm font-medium text-gray-700 mb-2">최신 수집 콘텐츠</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {data.sentimentAnalysis.samples.map((sample) => (
                    <div
                      key={sample.id}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                            sample.sentiment === 'positive'
                              ? 'bg-green-100 text-green-700'
                              : sample.sentiment === 'negative'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-gray-200 text-gray-700'
                          }`}>
                            {sample.sentiment === 'positive' ? '긍정' :
                             sample.sentiment === 'negative' ? '부정' : '중립'}
                          </span>
                          <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                            {sample.source === 'blog' ? '블로그' : '뉴스'}
                          </span>
                          {sample.isSponsored && (
                            <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                              협찬
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">{sample.publishedAt}</span>
                      </div>
                      <h4 className="font-medium text-sm text-gray-900 mb-1">{sample.title}</h4>
                      <p className="text-xs text-gray-600 line-clamp-2">{sample.snippet}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              title="감성 분석 데이터가 없습니다"
              description="블로그와 뉴스 콘텐츠를 수집 중입니다."
            />
          )}
        </div>
      </div>

      {/* YouTube 트렌드 섹션 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">YouTube 트렌드</h2>
            <span className="text-xs text-gray-500">24시간 캐싱 적용</span>
          </div>

          {data.youtubeVideos.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {data.youtubeVideos.map((video) => (
                <div
                  key={video.id}
                  className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  {video.thumbnailUrl && (
                    <div className="aspect-video bg-gray-200 rounded mb-2">
                      <img
                        src={video.thumbnailUrl}
                        alt={video.title}
                        className="w-full h-full object-cover rounded"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <h3 className="font-medium text-sm text-gray-900 line-clamp-2 mb-1">
                    {video.title}
                  </h3>
                  <p className="text-xs text-gray-600 mb-1">{video.channelName}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>조회수 {video.viewCount.toLocaleString()}</span>
                    <span>{video.uploadDate}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="YouTube 트렌드가 없습니다"
              description="관련 영상 데이터를 수집 중입니다."
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default TrendAnalysis;