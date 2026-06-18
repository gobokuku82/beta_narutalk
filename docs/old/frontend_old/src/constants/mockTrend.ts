import { TrendData } from '../types';

// 최근 30일 날짜 생성 헬퍼
const generateDates = (days: number = 30): string[] => {
  const dates: string[] = [];
  const today = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    dates.push(date.toISOString().split('T')[0]);
  }

  return dates;
};

// 클라이언트별 트렌드 목업 데이터
export const mockTrendData: Record<string, TrendData> = {
  '코스모스 뷰티': {
    keywords: [
      {
        keyword: '수분크림',
        values: [45, 48, 52, 55, 58, 61, 59, 57, 60, 65,
                 68, 72, 75, 78, 82, 85, 88, 91, 89, 87,
                 85, 83, 86, 88, 90, 92, 95, 98, 100, 97],
        dates: generateDates()
      },
      {
        keyword: '토너팩',
        values: [30, 32, 35, 38, 40, 42, 45, 48, 50, 52,
                 55, 58, 60, 62, 65, 68, 70, 72, 71, 69,
                 67, 65, 68, 70, 72, 75, 78, 80, 82, 85],
        dates: generateDates()
      },
      {
        keyword: '선크림',
        values: [55, 58, 60, 62, 65, 68, 70, 72, 75, 78,
                 80, 82, 85, 88, 90, 85, 80, 75, 70, 65,
                 60, 55, 50, 45, 40, 42, 45, 48, 50, 52],
        dates: generateDates()
      },
      {
        keyword: '비타민C세럼',
        values: [20, 22, 25, 28, 30, 32, 35, 38, 40, 42,
                 45, 48, 50, 52, 55, 58, 60, 62, 65, 68,
                 70, 72, 75, 78, 80, 78, 75, 72, 70, 68],
        dates: generateDates()
      },
      {
        keyword: '레티놀',
        values: [15, 18, 20, 22, 25, 28, 30, 32, 35, 38,
                 40, 42, 45, 48, 50, 48, 45, 42, 40, 38,
                 35, 32, 30, 32, 35, 38, 40, 42, 45, 48],
        dates: generateDates()
      }
    ],
    shoppingCategories: [
      {
        category: '기초화장품',
        clicks: [12000, 12500, 13000, 13500, 14000, 14500, 15000, 15500, 16000, 16500,
                17000, 17500, 18000, 18500, 19000, 19500, 20000, 19800, 19600, 19400,
                19200, 19000, 19200, 19400, 19600, 19800, 20000, 20200, 20400, 20600],
        dates: generateDates()
      },
      {
        category: '선케어',
        clicks: [8000, 8200, 8400, 8600, 8800, 9000, 9200, 9400, 9600, 9800,
                10000, 10200, 10400, 10600, 10800, 11000, 10800, 10600, 10400, 10200,
                10000, 9800, 9600, 9400, 9200, 9400, 9600, 9800, 10000, 10200],
        dates: generateDates()
      },
      {
        category: '세럼/에센스',
        clicks: [5000, 5100, 5200, 5300, 5400, 5500, 5600, 5700, 5800, 5900,
                6000, 6100, 6200, 6300, 6400, 6500, 6600, 6700, 6800, 6900,
                7000, 7100, 7200, 7300, 7400, 7500, 7600, 7700, 7800, 7900],
        dates: generateDates()
      }
    ],
    sentimentAnalysis: {
      positive: 65,
      negative: 10,
      neutral: 25,
      samples: [
        {
          id: 'blog-1',
          title: '코스모스 뷰티 수분크림 1개월 사용 후기',
          snippet: '정말 촉촉하고 좋아요! 피부가 완전 개선됐어요. 재구매 의사 100%입니다.',
          sentiment: 'positive',
          source: 'blog',
          isSponsored: false,
          publishedAt: '2024-03-15'
        },
        {
          id: 'news-1',
          title: '코스모스 뷰티, 친환경 패키징으로 MZ세대 사로잡다',
          snippet: '지속가능한 뷰티를 추구하는 코스모스 뷰티가 리필 가능한 용기를 출시하며 긍정적인 반응을 얻고 있다.',
          sentiment: 'positive',
          source: 'news',
          publishedAt: '2024-03-14'
        },
        {
          id: 'blog-2',
          title: '비타민C 세럼 비교 리뷰 (협찬)',
          snippet: '코스모스 뷰티 비타민C 세럼을 제공받아 사용해봤는데, 브라이트닝 효과가 확실해요.',
          sentiment: 'positive',
          source: 'blog',
          isSponsored: true,
          publishedAt: '2024-03-13'
        },
        {
          id: 'blog-3',
          title: '가격이 좀 비싸긴 하지만...',
          snippet: '효과는 좋은데 가격대가 높아서 계속 쓰기는 부담스러워요.',
          sentiment: 'negative',
          source: 'blog',
          isSponsored: false,
          publishedAt: '2024-03-12'
        },
        {
          id: 'news-2',
          title: '봄철 자외선 차단 필수템 5선',
          snippet: '코스모스 뷰티 선크림은 가벼운 제형으로 데일리 사용에 적합하다.',
          sentiment: 'neutral',
          source: 'news',
          publishedAt: '2024-03-11'
        }
      ]
    },
    youtubeVideos: [
      {
        id: 'yt-1',
        title: '✨수분크림 TOP 10 비교! 코스모스 뷰티 1위?!',
        viewCount: 285000,
        uploadDate: '2024-03-10',
        channelName: '뷰티 인사이더',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-2',
        title: '피부과 의사가 추천하는 레티놀 제품',
        viewCount: 156000,
        uploadDate: '2024-03-08',
        channelName: '닥터 스킨케어',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-3',
        title: '코스모스 뷰티 전 제품 리뷰 | 솔직 후기',
        viewCount: 98000,
        uploadDate: '2024-03-05',
        channelName: '언니의 화장대',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-4',
        title: '선크림 지속력 테스트 (충격적인 결과)',
        viewCount: 75000,
        uploadDate: '2024-03-03',
        channelName: '뷰티 실험실',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      }
    ]
  },

  '홈플렉스': {
    keywords: [
      {
        keyword: '무선청소기',
        values: [60, 62, 65, 68, 70, 72, 75, 78, 80, 82,
                 85, 88, 90, 92, 95, 98, 100, 98, 95, 92,
                 90, 88, 85, 82, 80, 82, 85, 88, 90, 92],
        dates: generateDates()
      },
      {
        keyword: '로봇청소기',
        values: [50, 52, 55, 58, 60, 62, 65, 68, 70, 72,
                 75, 78, 80, 82, 85, 88, 90, 88, 85, 82,
                 80, 78, 75, 72, 70, 72, 75, 78, 80, 82],
        dates: generateDates()
      },
      {
        keyword: '공기청정기',
        values: [40, 42, 45, 48, 50, 48, 45, 42, 40, 38,
                 35, 32, 30, 28, 25, 22, 20, 22, 25, 28,
                 30, 32, 35, 38, 40, 42, 45, 48, 50, 52],
        dates: generateDates()
      },
      {
        keyword: '에어프라이어',
        values: [35, 38, 40, 42, 45, 48, 50, 52, 55, 58,
                 60, 62, 65, 68, 70, 68, 65, 62, 60, 58,
                 55, 52, 50, 52, 55, 58, 60, 62, 65, 68],
        dates: generateDates()
      },
      {
        keyword: '전기포트',
        values: [25, 28, 30, 32, 35, 38, 40, 38, 35, 32,
                 30, 28, 25, 28, 30, 32, 35, 38, 40, 42,
                 45, 48, 50, 48, 45, 42, 40, 38, 35, 32],
        dates: generateDates()
      }
    ],
    shoppingCategories: [
      {
        category: '생활가전',
        clicks: [25000, 25500, 26000, 26500, 27000, 27500, 28000, 28500, 29000, 29500,
                30000, 30500, 31000, 31500, 32000, 32500, 33000, 32800, 32600, 32400,
                32200, 32000, 32200, 32400, 32600, 32800, 33000, 33200, 33400, 33600],
        dates: generateDates()
      },
      {
        category: '주방가전',
        clicks: [18000, 18200, 18400, 18600, 18800, 19000, 19200, 19400, 19600, 19800,
                20000, 20200, 20400, 20600, 20800, 21000, 20800, 20600, 20400, 20200,
                20000, 19800, 19600, 19800, 20000, 20200, 20400, 20600, 20800, 21000],
        dates: generateDates()
      },
      {
        category: '청소가전',
        clicks: [15000, 15300, 15600, 15900, 16200, 16500, 16800, 17100, 17400, 17700,
                18000, 18300, 18600, 18900, 19200, 19500, 19800, 20100, 20400, 20700,
                21000, 21300, 21600, 21900, 22200, 22500, 22800, 23100, 23400, 23700],
        dates: generateDates()
      }
    ],
    sentimentAnalysis: {
      positive: 72,
      negative: 8,
      neutral: 20,
      samples: [
        {
          id: 'blog-1',
          title: '홈플렉스 무선청소기 3개월 사용 후기',
          snippet: '흡입력 대박이고 배터리도 오래가요. 집안일이 너무 편해졌어요!',
          sentiment: 'positive',
          source: 'blog',
          isSponsored: false,
          publishedAt: '2024-03-15'
        },
        {
          id: 'news-1',
          title: '홈플렉스, 1분기 매출 전년 대비 35% 성장',
          snippet: '프리미엄 가전 브랜드 홈플렉스가 혁신적인 제품으로 시장 점유율을 확대하고 있다.',
          sentiment: 'positive',
          source: 'news',
          publishedAt: '2024-03-14'
        },
        {
          id: 'blog-2',
          title: '로봇청소기 비교 리뷰 (제품 협찬)',
          snippet: '홈플렉스 로봇청소기를 제공받아 사용해봤는데, 매핑 기능이 정말 똑똑해요.',
          sentiment: 'positive',
          source: 'blog',
          isSponsored: true,
          publishedAt: '2024-03-13'
        },
        {
          id: 'blog-3',
          title: '에어프라이어 소음이 좀 있네요',
          snippet: '요리는 잘 되는데 작동 소음이 생각보다 커서 아쉬워요.',
          sentiment: 'negative',
          source: 'blog',
          isSponsored: false,
          publishedAt: '2024-03-12'
        },
        {
          id: 'news-2',
          title: '봄맞이 가전제품 할인 특가전',
          snippet: '홈플렉스 제품이 최대 30% 할인된 가격으로 판매된다.',
          sentiment: 'neutral',
          source: 'news',
          publishedAt: '2024-03-11'
        }
      ]
    },
    youtubeVideos: [
      {
        id: 'yt-1',
        title: '무선청소기 끝판왕! 홈플렉스 V12 리뷰',
        viewCount: 425000,
        uploadDate: '2024-03-10',
        channelName: '가전 마스터',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-2',
        title: '로봇청소기 비교 테스트 | 과연 1위는?',
        viewCount: 312000,
        uploadDate: '2024-03-08',
        channelName: '테크 리뷰어',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-3',
        title: '홈플렉스 에어프라이어로 만든 100가지 요리',
        viewCount: 189000,
        uploadDate: '2024-03-05',
        channelName: '쿠킹 라이프',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-4',
        title: '공기청정기 필터 교체 주기와 관리법',
        viewCount: 95000,
        uploadDate: '2024-03-03',
        channelName: '생활의 달인',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      }
    ]
  },

  '스타일워크': {
    keywords: [
      {
        keyword: '운동화',
        values: [70, 72, 75, 78, 80, 82, 85, 88, 90, 92,
                 95, 98, 100, 98, 95, 92, 90, 88, 85, 82,
                 80, 78, 75, 78, 80, 82, 85, 88, 90, 92],
        dates: generateDates()
      },
      {
        keyword: '스니커즈',
        values: [65, 68, 70, 72, 75, 78, 80, 82, 85, 88,
                 90, 92, 95, 93, 90, 88, 85, 82, 80, 78,
                 75, 72, 70, 72, 75, 78, 80, 82, 85, 88],
        dates: generateDates()
      },
      {
        keyword: '캔버스화',
        values: [45, 48, 50, 52, 55, 58, 60, 62, 65, 68,
                 70, 68, 65, 62, 60, 58, 55, 52, 50, 48,
                 45, 48, 50, 52, 55, 58, 60, 62, 65, 68],
        dates: generateDates()
      },
      {
        keyword: '런닝화',
        values: [55, 58, 60, 62, 65, 68, 70, 72, 75, 78,
                 80, 82, 85, 88, 90, 88, 85, 82, 80, 78,
                 75, 72, 70, 72, 75, 78, 80, 82, 85, 88],
        dates: generateDates()
      },
      {
        keyword: '슬립온',
        values: [30, 32, 35, 38, 40, 42, 45, 48, 50, 52,
                 55, 58, 60, 58, 55, 52, 50, 48, 45, 42,
                 40, 38, 35, 38, 40, 42, 45, 48, 50, 52],
        dates: generateDates()
      }
    ],
    shoppingCategories: [
      {
        category: '스니커즈',
        clicks: [35000, 35500, 36000, 36500, 37000, 37500, 38000, 38500, 39000, 39500,
                40000, 40500, 41000, 41500, 42000, 42500, 43000, 42800, 42600, 42400,
                42200, 42000, 42200, 42400, 42600, 42800, 43000, 43200, 43400, 43600],
        dates: generateDates()
      },
      {
        category: '런닝화',
        clicks: [28000, 28300, 28600, 28900, 29200, 29500, 29800, 30100, 30400, 30700,
                31000, 31300, 31600, 31900, 32200, 32500, 32800, 33100, 33400, 33700,
                34000, 34300, 34600, 34900, 35200, 35500, 35800, 36100, 36400, 36700],
        dates: generateDates()
      },
      {
        category: '캐주얼화',
        clicks: [22000, 22200, 22400, 22600, 22800, 23000, 23200, 23400, 23600, 23800,
                24000, 24200, 24400, 24600, 24800, 25000, 24800, 24600, 24400, 24200,
                24000, 23800, 23600, 23800, 24000, 24200, 24400, 24600, 24800, 25000],
        dates: generateDates()
      }
    ],
    sentimentAnalysis: {
      positive: 78,
      negative: 5,
      neutral: 17,
      samples: [
        {
          id: 'blog-1',
          title: '스타일워크 신상 스니커즈 구매 후기',
          snippet: '디자인도 예쁘고 착화감도 최고! 발이 전혀 안 아파요. 강추합니다!',
          sentiment: 'positive',
          source: 'blog',
          isSponsored: false,
          publishedAt: '2024-03-15'
        },
        {
          id: 'news-1',
          title: '스타일워크, 친환경 소재 신발 라인 출시',
          snippet: '지속가능한 패션을 선도하는 스타일워크가 재활용 소재로 만든 신발을 선보였다.',
          sentiment: 'positive',
          source: 'news',
          publishedAt: '2024-03-14'
        },
        {
          id: 'blog-2',
          title: '런닝화 비교 리뷰 (브랜드 협찬)',
          snippet: '스타일워크 런닝화를 제공받아 한 달간 착용해봤는데, 쿠셔닝이 정말 좋아요.',
          sentiment: 'positive',
          source: 'blog',
          isSponsored: true,
          publishedAt: '2024-03-13'
        },
        {
          id: 'blog-3',
          title: '사이즈가 좀 작게 나온 것 같아요',
          snippet: '평소 사이즈로 주문했는데 살짝 작아요. 한 사이즈 크게 주문하세요.',
          sentiment: 'negative',
          source: 'blog',
          isSponsored: false,
          publishedAt: '2024-03-12'
        },
        {
          id: 'news-2',
          title: '봄 신상 스니커즈 트렌드',
          snippet: '스타일워크의 파스텔톤 스니커즈가 올봄 인기를 끌 것으로 예상된다.',
          sentiment: 'neutral',
          source: 'news',
          publishedAt: '2024-03-11'
        }
      ]
    },
    youtubeVideos: [
      {
        id: 'yt-1',
        title: '신발 덕후가 추천하는 스타일워크 BEST 5',
        viewCount: 567000,
        uploadDate: '2024-03-10',
        channelName: '슈즈 매니아',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-2',
        title: '3만원대 운동화 vs 30만원대 운동화 비교',
        viewCount: 423000,
        uploadDate: '2024-03-08',
        channelName: '가성비 리뷰',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-3',
        title: '스타일워크 전 제품 언박싱 & 착용 리뷰',
        viewCount: 234000,
        uploadDate: '2024-03-05',
        channelName: '패션 유튜버',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      },
      {
        id: 'yt-4',
        title: '운동화 관리법 | 10년 신는 비법',
        viewCount: 156000,
        uploadDate: '2024-03-03',
        channelName: '라이프 해커',
        thumbnailUrl: 'https://via.placeholder.com/320x180'
      }
    ]
  }
};

// 빈 데이터 생성 헬퍼 (Empty State 테스트용)
export const emptyTrendData: TrendData = {
  keywords: [],
  shoppingCategories: [],
  sentimentAnalysis: {
    positive: 0,
    negative: 0,
    neutral: 0,
    samples: []
  },
  youtubeVideos: []
};