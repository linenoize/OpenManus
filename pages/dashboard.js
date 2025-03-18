import Head from 'next/head';
import styles from '../styles/Dashboard.module.css';
import Header from '../components/Header';
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Dashboard() {
  const [services, setServices] = useState([
    { name: 'API Service', status: 'Checking...' },
    { name: 'Tools Service', status: 'Checking...' },
    { name: 'File Manager', status: 'Checking...' },
    { name: 'LLM Service', status: 'Checking...' },
    { name: 'Vector DB', status: 'Checking...' }
  ]);

  useEffect(() => {
    // Check services status
    const checkServices = async () => {
      try {
        const apiResponse = await axios.get('/api/health');
        const updatedServices = [...services];
        updatedServices[0].status = 'Online';
        
        try {
          const toolsResponse = await axios.get('/tools/health');
          updatedServices[1].status = 'Online';
        } catch (error) {
          updatedServices[1].status = 'Offline';
        }

        setServices(updatedServices);
      } catch (error) {
        const updatedServices = [...services];
        updatedServices[0].status = 'Offline';
        updatedServices[1].status = 'Offline';
        setServices(updatedServices);
      }
    };

    checkServices();
  }, []);

  return (
    <div className={styles.container}>
      <Head>
        <title>Dashboard - OpenManus</title>
        <meta name="description" content="OpenManus system dashboard" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header />

      <main className={styles.main}>
        <h1 className={styles.title}>System Dashboard</h1>

        <div className={styles.grid}>
          <div className={styles.serviceGrid}>
            <h2>Services Status</h2>
            <div className={styles.serviceList}>
              {services.map((service, index) => (
                <div key={index} className={styles.serviceItem}>
                  <span className={styles.serviceName}>{service.name}</span>
                  <span className={`${styles.serviceStatus} ${
                    service.status === 'Online' ? styles.online : 
                    service.status === 'Offline' ? styles.offline : styles.checking
                  }`}>
                    {service.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.controlPanel}>
            <h2>Control Panel</h2>
            <button className={styles.button}>Restart All Services</button>
            <button className={styles.button}>View System Logs</button>
            <button className={styles.button}>Configure System</button>
          </div>
        </div>
      </main>
    </div>
  );
}