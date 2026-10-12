import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import styles from './HomePage.module.css';
import { io } from 'socket.io-client';

// Interfaces for data structure
interface TelemetryData {
  cpuTemp: string;
  cpuUsage: string;
  memory: string;
  diskUsage: string;
  uptime: string;
}

interface DetectionData {
  threat: string;
  confidence: number;
  image: string;
  deterrentActive: string;
}

interface EventLogEntry {
  timestamp: string;
  message: string;
  animal: string;
  confidence: number;
  imageUrl: string;
  deterrent: string;
}

// Create socket instance OUTSIDE component - shared across all renders
const socket = io('http://localhost:5000', {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 10,
  autoConnect: true
});

function HomePage() {
  // State for all dynamic data
  const [telemetry, setTelemetry] = useState<TelemetryData>({
    cpuTemp: '0°C',
    cpuUsage: '0%',
    memory: '0GB / 0GB',
    diskUsage: '0% Used',
    uptime: 'Loading...'
  });

  const [liveDetection, setLiveDetection] = useState<DetectionData>(() => {
    const saved = localStorage.getItem('bear_event_log');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.length > 0) {
        return {
          threat: parsed[0].animal,
          confidence: parsed[0].confidence,
          image: parsed[0].imageUrl,
          deterrentActive: parsed[0].deterrent
        };
      }
    }
    return { threat: 'NONE', confidence: 0, image: '', deterrentActive: 'None' };
  });

  const [eventLog, setEventLog] = useState<EventLogEntry[]>(() => {
    const savedLog = localStorage.getItem('bear_event_log');
    return savedLog ? JSON.parse(savedLog) : [];
  });

  const [isConnected, setIsConnected] = useState(socket.connected);

  const [expandedEventIndex, setExpandedEventIndex] = useState<number | null>(null);

  // Handlers for control buttons
  const handleTriggerHorn = () => {
    console.log('📡 Sending Horn Trigger...');
    socket.emit('manual_trigger', { device: 'horn', action: 'toggle' });
  };

  const handleToggleLights = () => {
    console.log('📡 Sending Lights Trigger...');
    socket.emit('manual_trigger', { device: 'light', action: 'toggle' });
  };

  // WebSocket setup
  useEffect(() => {
    function onConnect() {
      console.log('✅ Connected to WebSocket server');
      setIsConnected(true);
    }

    function onDisconnect() {
      console.log('❌ Disconnected from WebSocket server');
      setIsConnected(false);
    }

    function onTelemetryUpdate(data: any) {
      console.log('📊 Received telemetry update:', data);
      
      // Calculate Memory in GB (since yolo.py sends bytes)
      const usedGB = (data.memory_used / (1024 ** 3)).toFixed(1);
      const totalGB = (data.memory_total / (1024 ** 3)).toFixed(0);

      setTelemetry({
        cpuTemp: `${data.cpu_temp}°C`, // yolo.py sends usage %, not temp
        cpuUsage: `${data.cpu_usage}%`, // yolo.py sends usage %, not temp
        memory: `${usedGB}GB / ${totalGB}GB`,
        diskUsage: `${data.disk_usage}%`, // Using RAM % as a proxy for load
        uptime: `${data.uptime}` // Last update time
      });
    }

    // Attach the listener
    socket.on('telemetry_update', onTelemetryUpdate);

    function onDetectionUpdate(data: any) {
      console.log('📸 Received detection update:', data);
      
      const confidence = parseFloat(data.confidence) || 0;
      const rawImageUrl = data.image_url || '';
      const animal = data.animal || 'UNKNOWN';
      const deterrent = data.deterrent || 'None';
      const imageUrl = data.image_url ? `${data.image_url}?t=${Date.now()}` : '';

      // 1. Update the live storage
      setLiveDetection({
        threat: animal,
        confidence: confidence,
        image: imageUrl,
        deterrentActive: deterrent
      });

      // 2. Add to event log
      const now = new Date();
      const timestamp = now.toTimeString().slice(0, 8);
      const newEntry: EventLogEntry = {
        timestamp,
        message: `DETECTED: ${animal.toUpperCase()} (${(confidence * 100).toFixed(0)}%) Action: ${deterrent}`,
        animal,
        confidence,
        imageUrl,
        deterrent
      };

      setEventLog(prev => {
        // Compare the NEW raw filename against the OLD filename (stripping the old timestamp)
        const lastEntryBaseUrl = prev.length > 0 ? prev[0].imageUrl.split('?')[0] : null;
        
        if (lastEntryBaseUrl === rawImageUrl) {
          return prev; // It's a duplicate, don't add
        }
        return [newEntry, ...prev.slice(0, 14)];
      });
      // Keep live panel independent from history expansion state
    }
    // Attach event listeners
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('detection_update', onDetectionUpdate);

    // Set initial connection state
    if (socket.connected) {
      setIsConnected(true);
    }

    // Cleanup - remove listeners but DON'T close the socket
    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('detection_update', onDetectionUpdate);
      socket.off('telemetry_update', onTelemetryUpdate);
      // DO NOT call socket.close() here!
    };
  }, []); // Empty dependency array - only run once on mount

  useEffect(() => {
    localStorage.setItem('bear_event_log', JSON.stringify(eventLog));
  }, [eventLog]);

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <h1 className={styles.title}>Bear-Be-Gone</h1>
        <div className={styles.logo}>UCONN</div>
      </header>

      {/* Main Content */}
      <main className={styles.mainContent}>
        <div className={styles.grid}>
          {/* Status & Controls Panel - Left Column */}
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>Status & Controls</h2>
            <div className={styles.panelContent}>
              <h3 className={styles.sectionHeading}>Telemetry Data</h3>
              <ul className={styles.telemetryList}>
                <li>CPU Temp: {telemetry.cpuTemp}</li>
                <li>CPU Usage: {telemetry.cpuUsage}</li>
                <li>Memory: {telemetry.memory}</li>
                <li>Disk Usage: {telemetry.diskUsage}</li>
                <li>Uptime: {telemetry.uptime}</li>
              </ul>

              <h3 className={styles.sectionHeading}>Manual Overrides</h3>
              <div className={styles.buttonGroup}>
                <button className={styles.controlButton} onClick={handleTriggerHorn}>TRIGGER HORN</button>
                <button className={styles.controlButton} onClick={handleToggleLights}>TOGGLE LIGHTS</button>
              </div>
            </div>
          </div>

          {/* Live Feed Panel - Center Column */}
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>Last Detection</h2>
            <div className={styles.panelContent}>
              <div className={isConnected ? styles.liveBadgeConnected : styles.liveBadgeDisconnected}>
                {isConnected ? '● LIVE FEED ACTIVE' : '● DISCONNECTED FROM BACKEND'}
              </div>

              <p className={styles.liveStatusText}>
                {liveDetection.threat !== 'NONE' 
                  ? `THREAT DETECTED: ${liveDetection.threat} ${(liveDetection.confidence * 100).toFixed(0)}%`
                  : 'No Threat Detected'}
              </p>

              <div className={styles.detectionFrame}>
                {liveDetection.image ? (
                  <img 
                    src={liveDetection.image} 
                    alt="Detection" 
                    className={styles.detectionImage}
                  />
                ) : (
                  <p className={styles.emptyDetectionText}>Waiting for Detection...</p>
                )}
              </div>

              <p className={styles.deterrentText}>
                Deterrent Sequence Active: {liveDetection.deterrentActive}
              </p>
            </div>
          </div>

          {/* Event Log Panel - Right Column */}
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>Event Log</h2>
            <div className={`${styles.panelContent} ${styles.eventLog}`}>
              {eventLog.length === 0 ? (
                <p className={styles.emptyEventLog}>No detections yet</p>
              ) : (
                eventLog.map((entry, index) => (
                  <div key={index} className={styles.eventItem}>
                    <button
                      className={`${styles.eventRowButton} ${expandedEventIndex === index ? styles.eventRowButtonActive : ''}`}
                      onClick={() => setExpandedEventIndex(expandedEventIndex === index ? null : index)}
                      type="button"
                    >
                      <span>{entry.timestamp} {entry.message}</span>
                      <span>{expandedEventIndex === index ? '▲' : '▼'}</span>
                    </button>

                    {expandedEventIndex === index && (
                      <div className={styles.eventPreview}>
                        <p><strong>Threat:</strong> {entry.animal} ({(entry.confidence * 100).toFixed(0)}%)</p>
                        <p><strong>Deterrent:</strong> {entry.deterrent}</p>
                        {entry.imageUrl ? (
                          <img src={entry.imageUrl} alt={`${entry.animal} detection`} className={styles.eventPreviewImage} />
                        ) : (
                          <p>No image available.</p>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* About Button */}
        <div className={styles.aboutButtonContainer}>
          <Link to="/about" className={styles.aboutButton}>
            About Our Project
          </Link>
        </div>
      </main>

      {/* Footer - Blue Bar */}
      <footer className={styles.footer}>
        <p className={styles.footerText}>Bear-Be-Gone Monitoring Dashboard</p>
      </footer>
    </div>
  );
}

export default HomePage;