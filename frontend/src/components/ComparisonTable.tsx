'use client';

import React from 'react';
import { ProductCard as ProductCardType, ComparisonData } from '@/types';
import styles from './ComparisonTable.module.css';

interface ComparisonTableProps {
    comparison: ComparisonData;
}

export default function ComparisonTable({ comparison }: ComparisonTableProps) {
    const { phones, winner_by_category } = comparison;

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(price);
    };

    const specs = [
        { key: 'price', label: 'Price', getValue: (p: ProductCardType) => formatPrice(p.price_inr) },
        { key: 'display', label: 'Display', getValue: (p: ProductCardType) => `${p.display_size}"` },
        { key: 'camera', label: 'Camera', getValue: (p: ProductCardType) => `${p.camera_main_mp}MP` },
        { key: 'battery', label: 'Battery', getValue: (p: ProductCardType) => `${p.battery_mah}mAh` },
        { key: 'ram', label: 'RAM', getValue: (p: ProductCardType) => `${p.ram_gb}GB` },
        { key: 'storage', label: 'Storage', getValue: (p: ProductCardType) => `${p.storage_gb}GB` },
        { key: 'rating', label: 'Rating', getValue: (p: ProductCardType) => `${p.rating.toFixed(1)} ★` },
    ];

    return (
        <div className={styles.container}>
            <h3 className={styles.title}>📊 Comparison</h3>

            <div className={styles.table}>
                {/* Header with phone names */}
                <div className={styles.headerRow}>
                    <div className={styles.specLabel}></div>
                    {phones.map((phone) => (
                        <div key={phone.id} className={styles.phoneHeader}>
                            <div className={styles.phoneBrand}>{phone.brand}</div>
                            <div className={styles.phoneModel}>{phone.model}</div>
                        </div>
                    ))}
                </div>

                {/* Spec rows */}
                {specs.map((spec) => (
                    <div key={spec.key} className={styles.row}>
                        <div className={styles.specLabel}>{spec.label}</div>
                        {phones.map((phone) => {
                            const isWinner = winner_by_category[`best_${spec.key}`] === phone.id;
                            return (
                                <div
                                    key={phone.id}
                                    className={`${styles.specValue} ${isWinner ? styles.winner : ''}`}
                                >
                                    {spec.getValue(phone)}
                                    {isWinner && <span className={styles.winnerBadge}>👑</span>}
                                </div>
                            );
                        })}
                    </div>
                ))}
            </div>

            {/* Key features */}
            <div className={styles.features}>
                <div className={styles.featuresTitle}>Key Features</div>
                <div className={styles.featuresGrid}>
                    {phones.map((phone) => (
                        <div key={phone.id} className={styles.phoneFeatures}>
                            <div className={styles.phoneFeatureHeader}>{phone.brand} {phone.model}</div>
                            <ul className={styles.featureList}>
                                {phone.key_features.slice(0, 3).map((feature, idx) => (
                                    <li key={idx}>{feature}</li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
