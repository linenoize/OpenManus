import Link from 'next/link';
import styles from '../styles/Header.module.css';

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.logo}>
        <Link href="/">
          OpenManus
        </Link>
      </div>
      <nav className={styles.nav}>
        <Link href="/" className={styles.navLink}>
          Home
        </Link>
        <Link href="/dashboard" className={styles.navLink}>
          Dashboard
        </Link>
        <Link href="/docs" className={styles.navLink}>
          Docs
        </Link>
      </nav>
    </header>
  );
}