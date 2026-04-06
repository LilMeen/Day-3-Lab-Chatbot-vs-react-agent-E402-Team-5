export interface ChatEntity {
    role: 'user' | 'chatbot';
    message: string;
    timestamp: Date;
}