"use client";

import React, { useEffect, useState, useRef } from 'react';
import { User } from 'lucide-react';

interface CursorData {
  user_id: string;
  username: string;
  cursor_position: number;
  selection_start: number;
  selection_end: number;
  timestamp: string;
}

interface CursorOverlayProps {
  editorRef: React.RefObject<HTMLDivElement>;
  cursors: CursorData[];
  currentUserId: string;
}

const CursorOverlay: React.FC<CursorOverlayProps> = ({
  editorRef,
  cursors,
  currentUserId
}) => {
  const [cursorPositions, setCursorPositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  const overlayRef = useRef<HTMLDivElement>(null);

  // Calculate cursor positions based on text position
  const calculateCursorPosition = (position: number) => {
    if (!editorRef.current) return { x: 0, y: 0 };

    try {
      // Create a temporary range to measure position
      const range = document.createRange();
      
      // Walk through all text nodes to find the correct position
      let currentPosition = 0;
      let targetNode = null;
      let targetOffset = 0;
      
      const walker = document.createTreeWalker(
        editorRef.current,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let node;
      while (node = walker.nextNode()) {
        const nodeLength = node.textContent?.length || 0;
        
        if (currentPosition + nodeLength >= position) {
          targetNode = node;
          targetOffset = position - currentPosition;
          break;
        }
        
        currentPosition += nodeLength;
      }
      
      // If we didn't find a specific node, use the last text node or create one at the end
      if (!targetNode) {
        targetNode = editorRef.current;
        targetOffset = editorRef.current.childNodes.length;
      }

      // Set range to the specified position
      range.setStart(targetNode, targetOffset);
      range.setEnd(targetNode, targetOffset);

      // Get bounding rectangle
      const rect = range.getBoundingClientRect();
      const editorRect = editorRef.current.getBoundingClientRect();

      const result = {
        x: rect.left - editorRect.left + (rect.width || 0),
        y: rect.top - editorRect.top
      };
      
      console.log(`Cursor position ${position}: x=${result.x}, y=${result.y}, rect=`, rect, 'editorRect=', editorRect);
      
      return result;
    } catch (error) {
      console.error('Error calculating cursor position:', error);
      // Fallback to a simple character-based calculation
      return calculateFallbackPosition(position);
    }
  };

  // Fallback position calculation using character width estimation
  const calculateFallbackPosition = (position: number) => {
    if (!editorRef.current) return { x: 0, y: 0 };
    
    try {
      // Estimate position based on average character width
      const editorRect = editorRef.current.getBoundingClientRect();
      const computedStyle = window.getComputedStyle(editorRef.current);
      const fontSize = parseInt(computedStyle.fontSize) || 16;
      const lineHeight = parseInt(computedStyle.lineHeight) || fontSize * 1.2;
      
      // Rough estimation: average character width is about 60% of font size
      const charWidth = fontSize * 0.6;
      
      // Calculate which line this position would be on
      const editorWidth = editorRect.width;
      const charsPerLine = Math.floor(editorWidth / charWidth);
      const line = Math.floor(position / charsPerLine);
      
      const x = (position % charsPerLine) * charWidth;
      const y = line * lineHeight;
      
      console.log(`Fallback cursor position ${position}: x=${x}, y=${y}, charWidth=${charWidth}, lineHeight=${lineHeight}`);
      
      return { x, y };
    } catch (error) {
      console.error('Error in fallback position calculation:', error);
      return { x: 0, y: 0 };
    }
  };

  // Update cursor positions when cursors change
  useEffect(() => {
    const newPositions = new Map<string, { x: number; y: number }>();
    
    cursors.forEach(cursor => {
      if (cursor.user_id !== currentUserId) {
        const position = calculateCursorPosition(cursor.cursor_position);
        newPositions.set(cursor.user_id, position);
      }
    });
    
    setCursorPositions(newPositions);
  }, [cursors, currentUserId]);

  // Recalculate positions when editor content changes
  useEffect(() => {
    if (cursors.length > 0) {
      // Small delay to ensure DOM is updated
      const timeout = setTimeout(() => {
        const newPositions = new Map<string, { x: number; y: number }>();
        
        cursors.forEach(cursor => {
          if (cursor.user_id !== currentUserId) {
            const position = calculateCursorPosition(cursor.cursor_position);
            newPositions.set(cursor.user_id, position);
          }
        });
        
        setCursorPositions(newPositions);
      }, 100);
      
      return () => clearTimeout(timeout);
    }
  }, [editorRef.current?.innerHTML]); // Recalculate when content changes

  // Generate user color based on user_id
  const getUserColor = (userId: string) => {
    const hash = userId.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return `hsl(${Math.abs(hash) % 360}, 70%, 50%)`;
  };

  return (
    <div 
      ref={overlayRef}
      className="absolute inset-0 pointer-events-none z-20"
      style={{ 
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0
      }}
    >
      {cursors
        .filter(cursor => cursor.user_id !== currentUserId)
        .map(cursor => {
          const position = cursorPositions.get(cursor.user_id);
          if (!position) return null;

          const userColor = getUserColor(cursor.user_id);
          const hasSelection = cursor.selection_start !== cursor.selection_end;

          return (
            <div
              key={cursor.user_id}
              className="absolute"
              style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
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
              
              {/* Selection Highlight */}
              {hasSelection && (
                <div 
                  className="absolute opacity-30 rounded-sm transition-all duration-150"
                  style={{ 
                    backgroundColor: userColor,
                    left: `${Math.min(cursor.selection_start, cursor.selection_end) - position.x}px`,
                    width: `${Math.abs(cursor.selection_end - cursor.selection_start)}px`,
                    height: '1.5rem',
                    top: '100%'
                  }}
                />
              )}
            </div>
          );
        })}
    </div>
  );
};

export default CursorOverlay;
