import { useState, useEffect } from 'react';
import { MapPin } from 'lucide-react';

interface TimeDisplayProps {
  location?: string;
}

const TimeDisplay = ({ location = "Corporate Office" }: TimeDisplayProps) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="text-center space-y-3">
      {/* Time - Primary visual element with enhanced emphasis */}
      <div className="relative">
        <p className="text-5xl md:text-6xl lg:text-7xl font-bold text-foreground tracking-tight animate-gentle-pulse">
          {formatTime(currentTime)}
        </p>
        {/* Subtle glow effect */}
        <div className="absolute inset-0 -z-10 blur-3xl opacity-20 bg-primary rounded-full scale-75" />
      </div>

      {/* Date */}
      <p className="text-base md:text-lg text-muted-foreground font-medium">
        {formatDate(currentTime)}
      </p>

      {/* Location */}
      <div className="flex items-center justify-center gap-1.5 text-muted-foreground pt-1">
        <MapPin className="w-4 h-4" />
        <span className="text-sm md:text-base font-medium">{location}</span>
      </div>
    </div>
  );
};

export default TimeDisplay;
