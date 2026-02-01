'use client';

import React from 'react';
import { ProductCard as ProductCardType } from '@/types';
import styles from './ProductCard.module.css';

interface ProductCardProps {
    product: ProductCardType;
    onClick?: () => void;
}

export default function ProductCard({ product, onClick }: ProductCardProps) {
    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(price);
    };

    return (
        <div className={styles.card} onClick={onClick}>
            <div className={styles.imageContainer}>
                <div className={styles.imagePlaceholder}>
                    <span className={styles.brandInitial}>{product.brand[0]}</span>
                </div>
                <div className={styles.rating}>
                    <span className={styles.star}>★</span>
                    <span>{product.rating.toFixed(1)}</span>
                </div>
            </div>

            <div className={styles.content}>
                <div className={styles.brand}>{product.brand}</div>
                <h3 className={styles.model}>{product.model}</h3>
                <div className={styles.price}>{formatPrice(product.price_inr)}</div>

                <div className={styles.specs}>
                    <div className={styles.specItem}>
                        <span className={styles.specIcon}>📱</span>
                        <span>{product.display_size}&quot;</span>
                    </div>
                    <div className={styles.specItem}>
                        <span className={styles.specIcon}>📷</span>
                        <span>{product.camera_main_mp}MP</span>
                    </div>
                    <div className={styles.specItem}>
                        <span className={styles.specIcon}>🔋</span>
                        <span>{product.battery_mah}mAh</span>
                    </div>
                    <div className={styles.specItem}>
                        <span className={styles.specIcon}>💾</span>
                        <span>{product.ram_gb}GB / {product.storage_gb}GB</span>
                    </div>
                </div>

                {product.key_features.length > 0 && (
                    <div className={styles.features}>
                        {product.key_features.slice(0, 2).map((feature, index) => (
                            <span key={index} className={styles.featureTag}>
                                {feature}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
