
import React, { useEffect, useState } from 'react';
import { User } from 'lucide-react';

interface CursorData {
  user_id: string;
  username: string;
  cursor_position: number;
  selection_start: number;
  selection_end: number;
  timestamp: string;
}

interface SimpleCursorOverlayProps {
  editorRef: React.RefObject<HTMLDivElement>;
  cursors: CursorData[];
  currentUserId: string;
}

const SimpleCursorOverlay: React.FC<SimpleCursorOverlayProps> = ({
  editorRef,
  cursors,
  currentUserId
}) => {
  const [cursorElements, setCursorElements] = useState<JSX.Element[]>([]);

  // Generate user color based on user_id
  const getUserColor = (userId: string) => {
    const hash = userId.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return `hsl(${Math.abs(hash) % 360}, 70%, 50%)`;
  };

  // Create cursor elements using a simpler approach
  useEffect(() => {
    if (!editorRef.current || cursors.length === 0) {
      setCursorElements([]);
      return;
    }

    const elements: JSX.Element[] = [];
    const editorRect = editorRef.current.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(editorRef.current);
    const fontSize = parseInt(computedStyle.fontSize) || 16;
    const lineHeight = parseInt(computedStyle.lineHeight) || fontSize * 1.2;
    const padding = parseInt(computedStyle.padding) || 24; // Default padding from prose class
    
    cursors
      .filter(cursor => cursor.user_id !== currentUserId)
      .forEach((cursor, index) => {
        const userColor = getUserColor(cursor.user_id);
        
        // Simple character-based positioning
        const charWidth = fontSize * 0.6; // Rough estimate
        const editorWidth = editorRect.width - (padding * 2);
        const charsPerLine = Math.floor(editorWidth / charWidth);
        
        const line = Math.floor(cursor.cursor_position / charsPerLine);
        const charInLine = cursor.cursor_position % charsPerLine;
        
        const x = padding + (charInLine * charWidth);
        const y = padding + (line * lineHeight);
        
        console.log(`Simple cursor ${cursor.username} at pos ${cursor.cursor_position}: x=${x}, y=${y}, line=${line}, charInLine=${charInLine}`);
        
        elements.push(
          <div
            key={cursor.user_id}
            className="absolute pointer-events-none z-30"
            style={{
              left: `${x}px`,
              top: `${y}px`,
              transform: 'translateY(-2px)'
            }}
          >
            {/* User Avatar and Name */}
            <div 
              className="flex items-center space-x-1 px-2 py-1 rounded-full shadow-md border-2 transition-all duration-200"
              style={{ 
                backgroundColor: `${userColor}20`,
                borderColor: userColor,
                color: userColor,
                backdropFilter: 'blur(4px)'
              }}
            >
              <User className="w-3 h-3" />
              <span className="text-xs font-medium whitespace-nowrap">
                {cursor.username}
              </span>
            </div>
            
            {/* Cursor Line */}
            <div 
              className="absolute w-0.5 h-6 animate-pulse"
              style={{ 
                backgroundColor: userColor,
                left: '50%',
                transform: 'translateX(-50%)',
                top: '100%'
              }}
            />
          </div>
        );
      });
    
    setCursorElements(elements);
  }, [cursors, currentUserId, editorRef]);

  return (
    <div className="absolute inset-0 pointer-events-none z-20">
      {cursorElements}
    </div>
  );
};

export default SimpleCursorOverlay;
