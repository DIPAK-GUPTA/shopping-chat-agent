'use client';

import React from 'react';
import { Message, ProductCard as ProductCardType, ComparisonData } from '@/types';
import ProductCard from './ProductCard';
import ComparisonTable from './ComparisonTable';
import styles from './ChatMessage.module.css';

interface ChatMessageProps {
    message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.role === 'user';

    // Simple markdown-like rendering
    const renderContent = (content: string) => {
        // Split by code blocks and process
        const parts = content.split(/(\*\*[^*]+\*\*)/g);

        return parts.map((part, index) => {
            // Bold text
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={index}>{part.slice(2, -2)}</strong>;
            }

            // Process line breaks and lists
            return part.split('\n').map((line, lineIndex) => {
                // Bullet points
                if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
                    return (
                        <li key={`${index}-${lineIndex}`} className={styles.listItem}>
                            {line.trim().slice(2)}
                        </li>
                    );
                }

                // Empty lines become breaks
                if (line.trim() === '') {
                    return <br key={`${index}-${lineIndex}`} />;
                }

                return (
                    <span key={`${index}-${lineIndex}`}>
                        {line}
                        {lineIndex < part.split('\n').length - 1 && <br />}
                    </span>
                );
            });
        });
    };

    return (
        <div className={`${styles.messageContainer} ${isUser ? styles.user : styles.assistant}`}>
            <div className={styles.avatar}>
                {isUser ? '👤' : '🤖'}
            </div>

            <div className={styles.messageContent}>
                <div className={styles.text}>
                    {renderContent(message.content)}
                </div>

                {/* Display products if available */}
                {message.products && message.products.length > 0 && (
                    <div className={styles.productsGrid}>
                        {message.products.map((product) => (
                            <ProductCard key={product.id} product={product} />
                        ))}
                    </div>
                )}

                {/* Display comparison table if available */}
                {message.comparison && (
                    <ComparisonTable comparison={message.comparison} />
                )}

                <div className={styles.timestamp}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
            </div>
        </div>
    );
}
