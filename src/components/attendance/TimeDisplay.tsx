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
    <div className="text-center space-y-2">
      {/* Location */}
      <div className="flex items-center justify-center gap-1.5 text-muted-foreground">
        <MapPin className="w-4 h-4" />
        <span className="text-sm md:text-base font-medium">{location}</span>
      </div>

      {/* Time */}
      <p className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground tracking-tight">
        {formatTime(currentTime)}
      </p>

      {/* Date */}
      <p className="text-sm md:text-base text-muted-foreground">
        {formatDate(currentTime)}
      </p>
    </div>
  );
};

export default TimeDisplay;
