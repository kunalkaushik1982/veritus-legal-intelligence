"use client";

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

interface DebugCursorOverlayProps {
  editorRef: React.RefObject<HTMLDivElement>;
  containerRef: React.RefObject<HTMLDivElement>;
  cursors: CursorData[];
  currentUserId: string;
}

const DebugCursorOverlay: React.FC<DebugCursorOverlayProps> = ({
  editorRef,
  containerRef,
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

  // Create a temporary cursor at the specified position to measure it
  const getCursorPosition = (position: number) => {
    if (!editorRef.current) {
      console.log('No editor ref');
      return { x: 0, y: 0 };
    }

    try {
      // Save current selection
      const selection = window.getSelection();
      const savedRange = selection && selection.rangeCount > 0 ? selection.getRangeAt(0).cloneRange() : null;

      // Create a temporary selection at the target position
      const range = document.createRange();
      
      // Get all text content and find the position
      const textContent = editorRef.current.textContent || '';
      const targetPosition = Math.min(position, textContent.length);
      
      
      // Walk through text nodes to find the correct position
      let currentPos = 0;
      const walker = document.createTreeWalker(
        editorRef.current,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let targetNode = null;
      let targetOffset = 0;
      
      let node;
      while (node = walker.nextNode()) {
        const nodeLength = node.textContent?.length || 0;
        if (currentPos + nodeLength >= targetPosition) {
          targetNode = node;
          targetOffset = targetPosition - currentPos;
          break;
        }
        currentPos += nodeLength;
      }
      
      if (targetNode) {
        range.setStart(targetNode, targetOffset);
        range.setEnd(targetNode, targetOffset);
        
        // Get the bounding rectangle
        const rect = range.getBoundingClientRect();
        const containerRect = containerRef.current?.getBoundingClientRect();
        
        if (!containerRect) {
          console.log('🔍 No container ref available');
          return { x: 0, y: 0 };
        }
        
        // Position relative to the container
        const result = {
          x: rect.left - containerRect.left + (rect.width || 0),
          y: rect.top - containerRect.top
        };
        
        console.log('🔍 Position calculation:', {
          rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
          containerRect: { left: containerRect.left, top: containerRect.top, width: containerRect.width, height: containerRect.height },
          result: result
        });
        
        
        // Restore selection
        if (savedRange && selection) {
          selection.removeAllRanges();
          selection.addRange(savedRange);
        }
        
        return result;
      } else {
        // Fallback: position at the end
        const editorRect = editorRef.current.getBoundingClientRect();
        return {
          x: editorRect.width - 50, // Right side with some margin
          y: editorRect.height - 30 // Bottom with some margin
        };
      }
    } catch (error) {
      console.error('Error getting cursor position:', error);
      return { x: 50, y: 50 }; // Fallback position
    }
  };

  useEffect(() => {
    if (!editorRef.current || cursors.length === 0) {
      setCursorElements([]);
      return;
    }

    const elements: JSX.Element[] = [];
    
    const filteredCursors = cursors.filter(cursor => cursor.user_id !== currentUserId);
    
    filteredCursors.forEach((cursor) => {
        const userColor = getUserColor(cursor.user_id);
        const position = getCursorPosition(cursor.cursor_position);
        
        
        elements.push(
          <div
            key={cursor.user_id}
            data-cursor-debug="true"
            className="absolute pointer-events-none z-30"
            style={{
              left: `${position.x}px`,
              top: `${position.y}px`,
              transform: 'translateY(-25px)', // Move avatar above the cursor line
              border: '2px solid red', // Debug border
              backgroundColor: 'rgba(255, 0, 0, 0.3)' // Debug background
            }}
          >
            {/* User Avatar and Name */}
            <div 
              className="flex items-center space-x-1 px-2 py-1 rounded-full shadow-md border-2"
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
              className="absolute w-0.5 h-6"
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
    <div 
      className="absolute inset-0 pointer-events-none z-20"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0
      }}
    >
      {cursorElements}
    </div>
  );
};

export default DebugCursorOverlay;
