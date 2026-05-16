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
    image: "/images/ui-cards.png",
    mockUrl: "https://shopwise.example.com/p/minimalist-yun-kaban",
    aiScore: 92
  },
  {
    id: "p2",
    name: "Saten Gece Elbisesi",
    brand: "Lumina",
    price: "₺2,150",
    image: "/images/crystal-bg.png",
    mockUrl: "https://shopwise.example.com/p/saten-gece-elbisesi",
    aiScore: 88
  },
  {
    id: "p3",
    name: "Deri Crossbody Çanta",
    brand: "Aura Milano",
    price: "₺1,899",
    image: "/images/navy_spheres.png",
    mockUrl: "https://shopwise.example.com/p/deri-crossbody-canta",
    aiScore: 95
  },
  {
    id: "p4",
    name: "Premium Sneaker",
    brand: "UrbanStride",
    price: "₺2,750",
    image: "/images/bg-navy.png",
    mockUrl: "https://shopwise.example.com/p/premium-sneaker",
    aiScore: 84
  }
];
