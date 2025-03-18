import Head from 'next/head';
import styles from '../styles/Home.module.css';
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  const [apiStatus, setApiStatus] = useState('Checking...');
  const [toolsStatus, setToolsStatus] = useState('Checking...');

  useEffect(() => {
    // Check API status
    axios.get('/api/health')
      .then(response => {
        setApiStatus('Online');
      })
      .catch(error => {
        setApiStatus('Offline');
      });

    // Check Tools status
    axios.get('/tools/health')
      .then(response => {
        setToolsStatus('Online');
      })
      .catch(error => {
        setToolsStatus('Offline');
      });
  }, []);

  return (
    <div className={styles.container}>
      <Head>
        <title>OpenManus</title>
        <meta name="description" content="OpenManus multi-agent system" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to <span className={styles.highlight}>OpenManus</span>
        </h1>

        <p className={styles.description}>
          A multi-agent system with plugin tools and LLM service
        </p>

        <div className={styles.grid}>
          <div className={styles.card}>
            <h2>API Status</h2>
            <p className={apiStatus === 'Online' ? styles.online : styles.offline}>
              {apiStatus}
            </p>
          </div>

          <div className={styles.card}>
            <h2>Tools Status</h2>
            <p className={toolsStatus === 'Online' ? styles.online : styles.offline}>
              {toolsStatus}
            </p>
          </div>

          <a href="/docs" className={styles.card}>
            <h2>Documentation &rarr;</h2>
            <p>Find detailed information about OpenManus features and API.</p>
          </a>

          <a href="/dashboard" className={styles.card}>
            <h2>Dashboard &rarr;</h2>
            <p>Access the system dashboard and controls.</p>
          </a>
        </div>
      </main>

      <footer className={styles.footer}>
        <a
          href="https://github.com/OpenManus"
          target="_blank"
          rel="noopener noreferrer"
        >
          OpenManus Project
        </a>
      </footer>
    </div>
  );
}