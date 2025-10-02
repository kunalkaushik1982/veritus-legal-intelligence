"use client";

import React from 'react';
import { User } from 'lucide-react';

interface UserCursorProps {
  user_id: string;
  username: string;
  cursor_position: number;
  selection_start?: number;
  selection_end?: number;
  isCurrentUser?: boolean;
  color?: string;
  avatar?: string;
}

const UserCursor: React.FC<UserCursorProps> = ({
  user_id,
  username,
  cursor_position,
  selection_start = cursor_position,
  selection_end = cursor_position,
  isCurrentUser = false,
  color = '#7c3aed',
  avatar
}) => {
  // Don't show cursor for current user (they see their own cursor)
  if (isCurrentUser) {
    return null;
  }

  // Generate user color if not provided
  const userColor = color || `hsl(${(user_id.charCodeAt(0) * 137.5) % 360}, 70%, 50%)`;

  return (
    <div className="absolute pointer-events-none z-10">
      {/* User Avatar */}
      <div 
        className="flex items-center space-x-1 px-2 py-1 rounded-full shadow-sm border"
        style={{ 
          backgroundColor: `${userColor}20`,
          borderColor: userColor,
          color: userColor
        }}
      >
        {avatar ? (
          <img 
            src={avatar} 
            alt={username}
            className="w-4 h-4 rounded-full"
          />
        ) : (
          <User className="w-4 h-4" />
        )}
        <span className="text-xs font-medium">{username}</span>
      </div>
      
      {/* Cursor Line */}
      <div 
        className="absolute w-0.5 h-6 animate-pulse"
        style={{ backgroundColor: userColor }}
      />
      
      {/* Selection Highlight (if there's a selection) */}
      {selection_start !== selection_end && (
        <div 
          className="absolute opacity-30 rounded-sm"
          style={{ 
            backgroundColor: userColor,
            left: `${Math.min(selection_start, selection_end)}px`,
            width: `${Math.abs(selection_end - selection_start)}px`,
            height: '1.5rem'
          }}
        />
      )}
    </div>
  );
};

export default UserCursor;
