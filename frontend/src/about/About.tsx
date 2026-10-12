import styles from './About.module.css';

function About() {
  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <h1 className={styles.title}>About Our Project</h1>
        <div className={styles.logo}>UCONN</div>
      </header>

      {/* Main Content */}
      <main className={styles.content}>
        {/* Why Section */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Why?</h2>
          
          <div className={styles.subsection}>
            <h3>The Problem:</h3>
            <p>The bear population has been rising sharply as time passes, especially in Connecticut. With an increase in population, there has also been an increase in home invasions. We hope to remedy this issue by designing a low-cost product that can intimidate bears into leaving homes alone to keep people safe.</p>
          </div>

          <div className={styles.subsection}>
            <h3>The Issue with Solutions:</h3>
            <ul>
              <li>Limited Deterrents: The current suggestions online and from others are limited to securing food and building small-scale defenses like electric fences. These are not sufficient to fend off bear invasions, especially if people or children are vulnerable outside.</li>
              <li>Home Invasions: Entries into homes continue to increase as time passes. In July, 2020, DEEP collected 25 reports of bears entering homes, more than any other year. Timeline of bear invasions shows a significant increase as time passes of these invasions.</li>
              <li>Need in Connecticut: In Connecticut, black bears are frequently found, to the point that in 2023, there were as many as 165 out of 169 towns reporting sightings.</li>
              <li>Rising Bear Population: Bear population statistics in Connecticut show an incline in their population, currently about 1,000 to 1,200, and may lose their fear of humans. They become more and more comfortable with humans, leading them into towns where the safety of the people is at risk.</li>
            </ul>
          </div>
        </section>

        {/* How Section */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>How?</h2>
          
          <div className={styles.subsection}>
            <h3>The Solution:</h3>
            <p>We have designed a device which combines visual processing via a camera, a motion sensor to detect activity, a raspberry pi which sends and receives signals from the components, and a compressed air horn to release noise and scare bears away.</p>
          </div>

          <div className={styles.subsection}>
            <h3>Our Components:</h3>
            <ul>
              <li>YOLO Version 11 and Camera: The software we use that recognizes bears from other animals or humans. It distinguishes them using our code and an attached camera that captures visuals when activated by the motion sensor.</li>
              <li>Raspberry Pi 5: This is our controlling component that receives signals from our hardware like the camera and processes it using our code to register certain actions, like releasing noise from the air horn upon detecting the bear.</li>
              <li>Compressed Air Horn: Our heavy-duty intimidation device that will release large amounts of noise to scare away the bear upon recognition by our visual processing software and hardware.</li>
              <li>Motion Sensor: Our motion sensor is on standby 24/7, ready to activate our visual processing unit upon detecting any activity so that as little power as possible is being used by our consumers.</li>
              <li>LED Lights: This will assist our horn in scaring the bear away in the night by lighting up the surroundings and intimidating the bear to run away.</li>
            </ul>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>By Justin Latif, Bryan Martinez, Jacob Bidorini, and Nathan Auten</p>
      </footer>
    </div>
  );
}

export default About;