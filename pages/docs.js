import Head from 'next/head';
import styles from '../styles/Docs.module.css';
import Header from '../components/Header';

export default function Docs() {
  return (
    <div className={styles.container}>
      <Head>
        <title>Documentation - OpenManus</title>
        <meta name="description" content="OpenManus documentation" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Header />

      <main className={styles.main}>
        <h1 className={styles.title}>Documentation</h1>

        <div className={styles.content}>
          <aside className={styles.sidebar}>
            <nav className={styles.nav}>
              <h3>Getting Started</h3>
              <ul>
                <li><a href="#introduction">Introduction</a></li>
                <li><a href="#installation">Installation</a></li>
                <li><a href="#configuration">Configuration</a></li>
              </ul>

              <h3>API Reference</h3>
              <ul>
                <li><a href="#api-overview">API Overview</a></li>
                <li><a href="#endpoints">Endpoints</a></li>
                <li><a href="#authentication">Authentication</a></li>
              </ul>

              <h3>Tools</h3>
              <ul>
                <li><a href="#file-manager">File Manager</a></li>
                <li><a href="#llm-service">LLM Service</a></li>
                <li><a href="#vector-db">Vector Database</a></li>
                <li><a href="#code-executor">Code Executor</a></li>
              </ul>
            </nav>
          </aside>

          <div className={styles.documentation}>
            <section id="introduction">
              <h2>Introduction</h2>
              <p>
                OpenManus is a multi-agent system with plugin tools and LLM service support.
                It provides a flexible architecture for building AI-powered applications
                with various capabilities including file management, document processing,
                code execution, and more.
              </p>
            </section>

            <section id="installation">
              <h2>Installation</h2>
              <p>
                To install OpenManus, you can use Docker for easy deployment:
              </p>
              <pre><code>
                docker-compose -f docker-compose.unified.yml up --build
              </code></pre>
              <p>
                For development, you can run the frontend and backend separately:
              </p>
              <pre><code>
                # Run backend
                python src/server.py

                # Run frontend
                npm run dev
              </code></pre>
            </section>

            <section id="configuration">
              <h2>Configuration</h2>
              <p>
                OpenManus can be configured through environment variables or configuration files.
                See the <code>.env.example</code> file for available options.
              </p>
            </section>

            <section id="api-overview">
              <h2>API Overview</h2>
              <p>
                The OpenManus API provides endpoints for interacting with the multi-agent system,
                managing files, executing code, and leveraging LLM capabilities.
              </p>
            </section>

            <section id="endpoints">
              <h2>Endpoints</h2>
              <p>
                The following endpoints are available:
              </p>
              <ul>
                <li><code>/api/health</code> - Check API health</li>
                <li><code>/api/agents</code> - Manage agents</li>
                <li><code>/api/tools</code> - Access tools</li>
                <li><code>/api/files</code> - Manage files</li>
              </ul>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}