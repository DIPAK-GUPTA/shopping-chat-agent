/**
 * API Service for communicating with the backend
 */
import { ChatRequest, ChatResponse, ProductCard } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiService {
    private sessionId: string | null = null;

    /**
     * Send a chat message to the AI agent
     */
    async sendMessage(message: string): Promise<ChatResponse> {
        const request: ChatRequest = {
            message,
            session_id: this.sessionId,
        };

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Chat request failed: ${response.statusText}`);
        }

        const data: ChatResponse = await response.json();

        // Store session ID for subsequent requests
        if (data.session_id) {
            this.sessionId = data.session_id;
        }

        return data;
    }

    /**
     * Get all products with optional filters
     */
    async getProducts(filters?: {
        brand?: string;
        min_price?: number;
        max_price?: number;
        sort_by?: string;
        limit?: number;
    }): Promise<ProductCard[]> {
        const params = new URLSearchParams();

        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, String(value));
                }
            });
        }

        const url = `${API_BASE_URL}/products${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Products request failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Get a specific product by ID
     */
    async getProduct(productId: string): Promise<ProductCard> {
        const response = await fetch(`${API_BASE_URL}/products/${productId}`);

        if (!response.ok) {
            throw new Error(`Product request failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Compare multiple products
     */
    async compareProducts(productIds: string[]): Promise<{
        phones: ProductCard[];
        highlights: Record<string, string>;
    }> {
        const response = await fetch(`${API_BASE_URL}/products/compare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(productIds),
        });

        if (!response.ok) {
            throw new Error(`Compare request failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Search products
     */
    async searchProducts(query: string, limit?: number): Promise<ProductCard[]> {
        const params = new URLSearchParams();
        if (limit) params.append('limit', String(limit));

        const response = await fetch(
            `${API_BASE_URL}/products/search/${encodeURIComponent(query)}?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`Search request failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Get available brands
     */
    async getBrands(): Promise<{ brands: string[] }> {
        const response = await fetch(`${API_BASE_URL}/products/brands`);

        if (!response.ok) {
            throw new Error(`Brands request failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Clear session
     */
    clearSession(): void {
        this.sessionId = null;
    }

    /**
     * Get current session ID
     */
    getSessionId(): string | null {
        return this.sessionId;
    }
}

// Export singleton instance
export const apiService = new ApiService();
