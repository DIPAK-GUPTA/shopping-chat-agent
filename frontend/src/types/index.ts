/**
 * Type definitions for Shopping Chat Agent
 */

export interface ProductCard {
    id: string;
    brand: string;
    model: string;
    price_inr: number;
    display_size: number;
    ram_gb: number;
    storage_gb: number;
    battery_mah: number;
    camera_main_mp: number;
    rating: number;
    image_url: string;
    key_features: string[];
}

export interface ComparisonData {
    phones: ProductCard[];
    comparison_table: Record<string, string>;
    winner_by_category: Record<string, string>;
}

export type QueryIntent =
    | 'search'
    | 'compare'
    | 'explain'
    | 'recommend'
    | 'details'
    | 'filter'
    | 'greeting'
    | 'off_topic'
    | 'adversarial'
    | 'unclear';

export interface ChatResponse {
    message: string;
    intent: QueryIntent;
    session_id: string;
    products?: ProductCard[] | null;
    comparison?: ComparisonData | null;
    sources: string[];
    is_refusal: boolean;
}

export interface ChatRequest {
    message: string;
    session_id?: string | null;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    products?: ProductCard[];
    comparison?: ComparisonData;
    isRefusal?: boolean;
}
