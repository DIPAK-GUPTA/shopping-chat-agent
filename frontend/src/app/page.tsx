'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Message } from '@/types';
import { ChatMessage } from '@/components';
import { apiService } from '@/services/api';
import styles from './page.module.css';

// Sample quick action queries
const QUICK_ACTIONS = [
  { label: '📷 Best Camera', query: 'Best camera phone under ₹30,000' },
  { label: '🔋 Battery King', query: 'Phone with best battery under ₹20,000' },
  { label: '⚡ Fast Charging', query: 'Phones with fast charging under ₹25,000' },
  { label: '🎮 Gaming', query: 'Best gaming phone under ₹40,000' },
  { label: '📱 Compact', query: 'Compact phone for one-hand use' },
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || isLoading) return;

    setError(null);

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiService.sendMessage(messageText);

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        products: response.products || undefined,
        comparison: response.comparison || undefined,
        isRefusal: response.is_refusal,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to send message. Please check if the backend is running.');

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ Sorry, I encountered an error. Please make sure the backend server is running on http://localhost:8000',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleQuickAction = (query: string) => {
    sendMessage(query);
  };

  const clearChat = () => {
    setMessages([]);
    apiService.clearSession();
  };

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>📱</span>
            <div>
              <h1 className={styles.title}>PhoneBot</h1>
              <p className={styles.subtitle}>AI Shopping Assistant</p>
            </div>
          </div>
          {messages.length > 0 && (
            <button className={styles.clearBtn} onClick={clearChat}>
              Clear Chat
            </button>
          )}
        </div>
      </header>

      {/* Chat Container */}
      <div className={styles.chatContainer}>
        {/* Welcome message if no messages */}
        {messages.length === 0 && (
          <div className={styles.welcome}>
            <div className={styles.welcomeIcon}>🤖</div>
            <h2 className={styles.welcomeTitle}>Welcome to PhoneBot!</h2>
            <p className={styles.welcomeText}>
              I can help you find, compare, and learn about mobile phones.
              Try asking me something like:
            </p>
            <div className={styles.exampleQueries}>
              <div className={styles.exampleItem}>&quot;Best camera phone under ₹30,000&quot;</div>
              <div className={styles.exampleItem}>&quot;Compare Pixel 8a vs OnePlus 12R&quot;</div>
              <div className={styles.exampleItem}>&quot;What is OIS?&quot;</div>
            </div>

            {/* Quick Actions */}
            <div className={styles.quickActions}>
              {QUICK_ACTIONS.map((action, index) => (
                <button
                  key={index}
                  className={styles.quickActionBtn}
                  onClick={() => handleQuickAction(action.query)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className={styles.messages}>
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className={styles.loadingMessage}>
              <div className={styles.loadingAvatar}>🤖</div>
              <div className={styles.loadingDots}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className={styles.errorBanner}>
          {error}
        </div>
      )}

      {/* Input Form */}
      <form className={styles.inputForm} onSubmit={handleSubmit}>
        <div className={styles.inputContainer}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about phones... (e.g., 'Best camera under ₹30k')"
            className={styles.input}
            disabled={isLoading}
          />
          <button
            type="submit"
            className={styles.sendBtn}
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? '...' : '➤'}
          </button>
        </div>
      </form>
    </main>
  );
}
