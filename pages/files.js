import { useState, useEffect } from 'react';
import Head from 'next/head';
import Header from '../components/Header';
import styles from '../styles/Files.module.css';

export default function Files() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPath, setCurrentPath] = useState('/');
  const [error, setError] = useState(null);
  
  // Simulated data for demonstration
  const mockFiles = [
    { name: 'document.txt', type: 'file', size: '24 KB', modified: '2025-03-16' },
    { name: 'project.py', type: 'file', size: '12 KB', modified: '2025-03-15' },
    { name: 'images', type: 'directory', modified: '2025-03-12' },
    { name: 'data.json', type: 'file', size: '8 KB', modified: '2025-03-10' },
    { name: 'notes.md', type: 'file', size: '4 KB', modified: '2025-03-05' },
  ];
  
  useEffect(() => {
    // Simulate API fetch with a delay
    const fetchFiles = async () => {
      setLoading(true);
      
      try {
        // In a real implementation, this would be an API call
        // const response = await fetch('/api/files?path=' + currentPath);
        // const data = await response.json();
        
        // Using mock data for now
        setTimeout(() => {
          setFiles(mockFiles);
          setLoading(false);
        }, 800);
      } catch (err) {
        setError('Failed to fetch files. Please try again.');
        setLoading(false);
      }
    };
    
    fetchFiles();
  }, [currentPath]);
  
  const navigateToFolder = (folderName) => {
    setCurrentPath((prevPath) => {
      if (prevPath === '/') {
        return `/${folderName}`;
      }
      return `${prevPath}/${folderName}`;
    });
  };
  
  const navigateUp = () => {
    setCurrentPath((prevPath) => {
      if (prevPath === '/') return '/';
      
      const parts = prevPath.split('/');
      parts.pop();
      return parts.join('/') || '/';
    });
  };
  
  return (
    <div className={styles.container}>
      <Head>
        <title>File Manager - OpenManus</title>
        <meta name="description" content="OpenManus file management system" />
      </Head>
      
      <Header />
      
      <main className={styles.main}>
        <div className={styles.header}>
          <h1>File Manager</h1>
          <div className={styles.pathNavigation}>
            <button 
              className={styles.navButton} 
              onClick={navigateUp}
              title="Navigate up one level"
            >
              ⬆️
            </button>
            <div className={styles.currentPath}>
              {currentPath}
            </div>
          </div>
        </div>
        
        {error && (
          <div className={styles.error}>
            {error}
          </div>
        )}
        
        {loading ? (
          <div className={styles.loading}>Loading files...</div>
        ) : (
          <div className={styles.fileList}>
            <div className={styles.fileHeader}>
              <div className={styles.fileName}>Name</div>
              <div className={styles.fileType}>Type</div>
              <div className={styles.fileSize}>Size</div>
              <div className={styles.fileModified}>Modified</div>
            </div>
            
            {files.map((file) => (
              <div key={file.name} className={styles.fileItem}>
                <div className={styles.fileName}>
                  {file.type === 'directory' ? (
                    <button
                      className={styles.folderButton}
                      onClick={() => navigateToFolder(file.name)}
                    >
                      📁 {file.name}
                    </button>
                  ) : (
                    <span>📄 {file.name}</span>
                  )}
                </div>
                <div className={styles.fileType}>{file.type}</div>
                <div className={styles.fileSize}>{file.size || '-'}</div>
                <div className={styles.fileModified}>{file.modified}</div>
              </div>
            ))}
            
            {files.length === 0 && (
              <div className={styles.emptyMessage}>
                No files found in this directory.
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}