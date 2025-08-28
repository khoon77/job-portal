export default function handler(req, res) {
  if (req.method === 'GET') {
    const jobs = [
      {
        id: 1,
        title: "2024년 서울시 9급 공무원 채용",
        institution: "서울특별시",
        location: "서울시 전체",
        deadline: "2024-12-31",
        status: "접수중"
      },
      {
        id: 2,
        title: "국민연금공단 계약직 직원 채용",
        institution: "국민연금공단", 
        location: "전국",
        deadline: "2024-12-25",
        status: "접수중"
      }
    ];

    res.status(200).json({ success: true, data: jobs });
  } else {
    res.status(405).json({ message: 'Method not allowed' });
  }
}