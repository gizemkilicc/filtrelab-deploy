export type Product = {
  id: string;
  name: string;
  brand: string;
  price: string;
  image: string;
  mockUrl: string;
  aiScore: number;
};

export const featuredProducts: Product[] = [
  {
    id: "p1",
    name: "Minimalist Yün Kaban",
    brand: "Nordic Atelier",
    price: "₺3,499",
    image: "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    mockUrl: "https://shopwise.example.com/p/minimalist-yun-kaban",
    aiScore: 92
  },
  {
    id: "p2",
    name: "Saten Gece Elbisesi",
    brand: "Lumina",
    price: "₺2,150",
    image: "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    mockUrl: "https://shopwise.example.com/p/saten-gece-elbisesi",
    aiScore: 88
  },
  {
    id: "p3",
    name: "Deri Crossbody Çanta",
    brand: "Aura Milano",
    price: "₺1,899",
    image: "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    mockUrl: "https://shopwise.example.com/p/deri-crossbody-canta",
    aiScore: 95
  },
  {
    id: "p4",
    name: "Premium Sneaker",
    brand: "UrbanStride",
    price: "₺2,750",
    image: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    mockUrl: "https://shopwise.example.com/p/premium-sneaker",
    aiScore: 84
  }
];
