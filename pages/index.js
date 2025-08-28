import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function Home() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 기존 Firebase 데이터를 정적으로 로드
    const mockJobs = [
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
    
    setTimeout(() => {
      setJobs(mockJobs);
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return <div style={{textAlign: 'center', padding: '50px'}}>로딩 중...</div>;
  }

  return (
    <>
      <Head>
        <title>공공일터 채용정보</title>
        <meta name="description" content="공공기관 채용정보를 한눈에" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div style={{
        fontFamily: 'Arial, sans-serif',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px'
      }}>
        <h1 style={{
          textAlign: 'center',
          color: '#1976d2',
          marginBottom: '40px'
        }}>
          공공일터 채용정보
        </h1>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: '20px'
        }}>
          {jobs.map(job => (
            <div key={job.id} style={{
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '20px',
              backgroundColor: '#fff',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{color: '#1976d2', marginBottom: '10px'}}>
                {job.title}
              </h3>
              <p><strong>기관:</strong> {job.institution}</p>
              <p><strong>근무지:</strong> {job.location}</p>
              <p><strong>마감일:</strong> {job.deadline}</p>
              <span style={{
                backgroundColor: '#4caf50',
                color: 'white',
                padding: '5px 10px',
                borderRadius: '4px',
                fontSize: '14px'
              }}>
                {job.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}