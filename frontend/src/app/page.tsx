import Navbar from "@/components/landing/Navbar";
import HeroSection from "@/components/landing/HeroSection";
import MetricsStrip from "@/components/landing/MetricsStrip";
import Footer from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <>
      <div className="bg-mesh" />
      <main style={{ minHeight: "100vh", position: "relative" }}>
        <Navbar />
        <HeroSection />
        <MetricsStrip />
        <Footer />
      </main>
    </>
  );
}
