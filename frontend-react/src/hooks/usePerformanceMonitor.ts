import { useState, useEffect } from 'react';

export const usePerformanceMonitor = () => {
  const [isLowPerf, setIsLowPerf] = useState(false);

  useEffect(() => {
    let frames = 0;
    let lastTime = performance.now();
    let lowPerfCount = 0;
    let animationFrameId: number;

    const checkPerformance = () => {
      const time = performance.now();
      frames++;

      if (time - lastTime >= 1000) {
        const fps = frames;
        if (fps < 35) {
          lowPerfCount++;
        } else {
          lowPerfCount = 0;
        }

        if (lowPerfCount >= 3) {
          setIsLowPerf(true);
          return; 
        }

        frames = 0;
        lastTime = time;
      }

      animationFrameId = requestAnimationFrame(checkPerformance);
    };

    animationFrameId = requestAnimationFrame(checkPerformance);

    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  return isLowPerf;
};
