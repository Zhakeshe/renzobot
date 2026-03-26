import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Star, 
  ShieldCheck, 
  LayoutGrid, 
  User, 
  Wallet, 
  ArrowRight, 
  ChevronRight,
  History,
  Info,
  Loader2,
  AlertCircle,
  BarChart3,
  Users,
  ShoppingCart,
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  ChevronLeft
} from 'lucide-react';
import { cn } from './lib/utils';

// --- Components ---

const Card = ({ children, className, onClick }: { children: React.ReactNode, className?: string, onClick?: () => void, key?: any }) => (
  <div 
    onClick={onClick}
    className={cn("bg-slate-800/40 border border-slate-700/50 rounded-2xl p-4", className)}
  >
    {children}
  </div>
);

const Button = ({ children, onClick, variant = 'primary', className, disabled, loading }: any) => {
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-500 text-white",
    secondary: "bg-slate-800 hover:bg-slate-700 text-slate-200",
    outline: "border border-slate-700 hover:bg-slate-800 text-slate-300"
  };

  return (
    <button 
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        "w-full py-3 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100",
        variants[variant as keyof typeof variants],
        className
      )}
    >
      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : children}
    </button>
  );
};

// --- Main App ---

export default function App() {
  const [activeTab, setActiveTab] = useState('shop');
  const [view, setView] = useState('main'); // 'main', 'nft_list', 'nft_detail'
  const [userData, setUserData] = useState<any>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [nftCollections, setNftCollections] = useState<any[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<any>(null);
  const [nftItems, setNftItems] = useState<any[]>([]);
  const [selectedNft, setSelectedNft] = useState<any>(null);
  const [nftLoading, setNftLoading] = useState(false);
  const [adminStats, setAdminStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null);
  const [rentDays, setRentDays] = useState(1);

  const tg = (window as any).Telegram?.WebApp;

  const fetchNftCollections = async () => {
    try {
      const res = await fetch('/api/nft/collections');
      const data = await res.json();
      if (data.success) {
        setNftCollections(data.collections);
      }
    } catch (err) {
      console.error("Failed to fetch collections", err);
    }
  };

  const fetchNftItems = async (colAddress: string) => {
    setNftLoading(true);
    try {
      const res = await fetch(`/api/nft/list?collection_address=${colAddress}`);
      const data = await res.json();
      if (data.success) {
        setNftItems(data.items);
      }
    } catch (err) {
      console.error("Failed to fetch NFT items", err);
    } finally {
      setNftLoading(false);
    }
  };

  const fetchData = useCallback(async () => {
    try {
      const userId = tg?.initDataUnsafe?.user?.id || 123;
      const initData = tg?.initData || "";

      const [userRes, prodRes] = await Promise.all([
        fetch(`/api/user/${userId}`, { headers: { 'x-telegram-init-data': initData } }),
        fetch(`/api/products`)
      ]);

      if (!userRes.ok) throw new Error("Пайдаланушы табылмады");
      
      const userData = await userRes.json();
      const productsData = await prodRes.json();

      setUserData(userData);
      setProducts(productsData);
      
      await fetchNftCollections();

      // Егер админ болса, статистиканы жүктеу
      if (userData.is_admin) {
        const statsRes = await fetch('/api/admin/stats', {
          headers: { 'x-user-id': userId.toString() }
        });
        if (statsRes.ok) {
          setAdminStats(await statsRes.json());
        }
      }

      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [tg]);

  useEffect(() => {
    fetchData();
    tg?.expand();
  }, [fetchData, tg]);

  const handleBuy = async (product: any) => {
    if (product.id === 'nft') {
      setActiveTab('nft');
      setView('main');
      return;
    }
    const userId = tg?.initDataUnsafe?.user?.id || 123;
    
    tg?.showConfirm(`Сіз ${product.name} сатып алғыңыз келе ме?`, async (confirmed: boolean) => {
      if (confirmed) {
        try {
          const res = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              userId,
              productId: product.id,
              amountKzt: product.price_kzt,
              quantity: 1
            })
          });

          if (res.ok) {
            tg?.showAlert("Тапсырыс қабылданды! Бот хабарлама жібереді.");
            fetchData(); // Балансты жаңарту
          } else {
            const data = await res.json();
            tg?.showAlert(data.error || "Қате орын алды");
          }
        } catch (err) {
          tg?.showAlert("Сервермен байланыс жоқ");
        }
      }
    });
  };

  const handleRentNft = async () => {
    if (!selectedNft) return;
    const userId = tg?.initDataUnsafe?.user?.id || 123;
    const amountKzt = selectedNft.price_per_day_kzt * rentDays;

    tg?.showConfirm(`Сіз ${selectedNft.name} ${rentDays} күнге жалдағыңыз келе ме?`, async (confirmed: boolean) => {
      if (confirmed) {
        try {
          const res = await fetch('/api/nft/rent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              userId,
              nft_address: selectedNft.address,
              days: rentDays,
              amountKzt
            })
          });

          if (res.ok) {
            tg?.showAlert("Жалдау сәтті орындалды! Бот хабарлама жібереді.");
            setView('main');
            fetchData();
          } else {
            const data = await res.json();
            tg?.showAlert(data.error || "Қате орын алды");
          }
        } catch (err) {
          tg?.showAlert("Сервермен байланыс жоқ");
        }
      }
    });
  };

  const renderNftCatalog = () => {
    if (view === 'nft_list') {
      return (
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-4"
        >
          <div className="flex items-center gap-3 mb-6">
            <button onClick={() => setView('main')} className="p-2 bg-slate-800 rounded-full hover:bg-slate-700 transition-colors">
              <ChevronLeft className="w-6 h-6" />
            </button>
            <div>
              <h2 className="text-xl font-bold line-clamp-1">{selectedCollection?.name}</h2>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Каталог</p>
            </div>
          </div>

          <div className="bg-slate-800/40 p-4 rounded-2xl border border-slate-700/30 mb-6">
            <p className="text-sm text-slate-300 leading-relaxed">{selectedCollection?.description}</p>
            <div className="flex gap-4 mt-4">
              <div className="flex-1 bg-slate-900/50 p-2 rounded-xl text-center border border-slate-700/20">
                <p className="text-[10px] text-slate-500 uppercase">Барлығы</p>
                <p className="font-bold text-blue-400">{selectedCollection?.items_count || '...'}</p>
              </div>
              <div className="flex-1 bg-slate-900/50 p-2 rounded-xl text-center border border-slate-700/20">
                <p className="text-[10px] text-slate-500 uppercase">Сыйлық</p>
                <p className="font-bold text-purple-400">NFT</p>
              </div>
            </div>
          </div>

          {nftLoading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
              <p className="text-slate-500 text-sm animate-pulse">NFT жүктелуде...</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {nftItems.map((nft) => (
                <Card 
                  key={nft.address} 
                  className="p-2 overflow-hidden active:scale-95 transition-all hover:border-blue-500/50 group"
                  onClick={() => {
                    setSelectedNft(nft);
                    setRentDays(nft.min_days || 1);
                    setView('nft_detail');
                  }}
                >
                  <div className="relative aspect-square mb-3 overflow-hidden rounded-xl">
                    <img 
                      src={nft.image_url} 
                      alt={nft.name} 
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                      referrerPolicy="no-referrer" 
                    />
                    <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded-lg text-[10px] font-bold text-white border border-white/10">
                      #{nft.name.split('#')[1] || '...'}
                    </div>
                  </div>
                  <div className="px-1 pb-1">
                    <div className="text-[10px] text-slate-500 mb-0.5 uppercase tracking-tighter truncate">{nft.name}</div>
                    <div className="text-sm font-bold text-blue-400">{nft.price_per_day_kzt.toFixed(0)} ₸ <span className="text-[10px] text-slate-500 font-normal">/ күн</span></div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </motion.div>
      );
    }

    if (view === 'nft_detail') {
      return (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <button onClick={() => setView('nft_list')} className="p-2 bg-slate-800 rounded-full hover:bg-slate-700 transition-colors">
              <ChevronLeft className="w-6 h-6" />
            </button>
            <h2 className="text-xl font-bold">NFT Мәліметі</h2>
          </div>

          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-[2rem] blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <img 
              src={selectedNft?.image_url} 
              alt={selectedNft?.name} 
              className="relative w-full aspect-square object-cover rounded-[2rem] shadow-2xl border border-slate-700/50" 
              referrerPolicy="no-referrer" 
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-start">
              <h1 className="text-2xl font-bold text-white">{selectedNft?.name}</h1>
              <div className="bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full text-xs font-bold border border-blue-500/20">
                Fragment
              </div>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">{selectedNft?.description || 'Telegram сыйлық NFT-і. Жалға алу арқылы профиліңізге қоя аласыз.'}</p>
          </div>

          <Card className="bg-slate-800/40 border-slate-700/30">
            <h3 className="text-[10px] font-bold text-slate-500 mb-4 uppercase tracking-[0.2em]">Сипаттамалары</h3>
            <div className="grid grid-cols-2 gap-3">
              {selectedNft?.attributes?.map((attr: any, i: number) => (
                <div key={i} className="bg-slate-900/40 p-3 rounded-2xl border border-slate-700/20">
                  <div className="text-[9px] text-slate-500 uppercase mb-1 font-bold">{attr.trait_type}</div>
                  <div className="text-sm font-semibold text-slate-200">{attr.value}</div>
                </div>
              ))}
              {(!selectedNft?.attributes || selectedNft.attributes.length === 0) && (
                <p className="col-span-2 text-center text-slate-600 text-xs italic py-2">Сипаттамалар жоқ</p>
              )}
            </div>
          </Card>

          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 p-6 rounded-[2rem] space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <span className="text-slate-400 text-sm block">Жалдау мерзімі</span>
                <span className="text-[10px] text-slate-500 uppercase">Күндер саны</span>
              </div>
              <div className="flex items-center gap-4 bg-slate-800 rounded-2xl p-1.5 border border-slate-700/50">
                <button 
                  onClick={() => setRentDays(Math.max(selectedNft?.min_days || 1, rentDays - 1))} 
                  className="w-10 h-10 flex items-center justify-center bg-slate-700 hover:bg-slate-600 rounded-xl transition-colors text-xl font-bold"
                >
                  -
                </button>
                <span className="w-8 text-center font-bold text-lg">{rentDays}</span>
                <button 
                  onClick={() => setRentDays(rentDays + 1)} 
                  className="w-10 h-10 flex items-center justify-center bg-slate-700 hover:bg-slate-600 rounded-xl transition-colors text-xl font-bold"
                >
                  +
                </button>
              </div>
            </div>
            
            <div className="h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent"></div>

            <div className="flex justify-between items-center">
              <span className="text-slate-400 font-medium">Жалпы сома:</span>
              <div className="text-right">
                <span className="text-2xl font-bold text-blue-400">{(selectedNft?.price_per_day_kzt * rentDays).toFixed(0)} ₸</span>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Баланстан алынады</p>
              </div>
            </div>

            <Button onClick={handleRentNft} className="bg-blue-600 hover:bg-blue-500 h-16 text-lg font-bold rounded-2xl shadow-lg shadow-blue-600/20 active:scale-95 transition-all">
              Жалға алу
            </Button>
          </div>
        </motion.div>
      );
    }

    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div className="relative mb-8">
          <div className="absolute -inset-4 bg-blue-600/10 blur-3xl rounded-full"></div>
          <h2 className="relative text-2xl font-black text-white tracking-tight">NFT Коллекциялар</h2>
          <p className="relative text-sm text-slate-500">Жалға алуға болатын сыйлықтар</p>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {nftCollections.filter(c => !c.name.toLowerCase().includes('username') && !c.name.toLowerCase().includes('number')).map((col) => (
            <Card 
              key={col.address} 
              className="relative group overflow-hidden border-slate-800/50 hover:border-blue-500/30 transition-all duration-300"
              onClick={() => {
                setSelectedCollection(col);
                fetchNftItems(col.address || col.nft_address);
                setView('nft_list');
              }}
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/5 blur-3xl -mr-16 -mt-16 group-hover:bg-blue-600/10 transition-colors"></div>
              <div className="relative flex items-center gap-5 p-1">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-2xl flex items-center justify-center border border-white/5 group-hover:scale-110 transition-transform duration-500">
                  <LayoutGrid className="w-8 h-8 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-lg text-slate-100 group-hover:text-blue-400 transition-colors truncate">{col.name}</h3>
                  <p className="text-xs text-slate-500 line-clamp-1 mt-0.5">{col.description}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-[10px] font-bold bg-slate-800 text-slate-400 px-2 py-0.5 rounded-md border border-slate-700/50">
                      {col.items_count || '...'} NFT
                    </span>
                    <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">Көру</span>
                  </div>
                </div>
                <div className="bg-slate-800/50 p-2 rounded-xl group-hover:bg-blue-600 transition-all group-hover:translate-x-1">
                  <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-white" />
                </div>
              </div>
            </Card>
          ))}
          {nftCollections.length === 0 && (
            <div className="text-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-slate-700 mx-auto mb-4" />
              <p className="text-slate-600 text-sm">Коллекциялар жүктелуде...</p>
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  if (loading) return (
    <div className="min-h-screen bg-[#0f172a] flex flex-col items-center justify-center text-white gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
      <p className="text-slate-400 animate-pulse">Деректер жүктелуде...</p>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-[#0f172a] flex flex-col items-center justify-center text-white p-6 text-center gap-4">
      <AlertCircle className="w-12 h-12 text-red-500" />
      <h2 className="text-xl font-bold">Қате орын алды</h2>
      <p className="text-slate-400">{error}</p>
      <Button onClick={fetchData} variant="outline">Қайталау</Button>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0f172a]/80 backdrop-blur-md border-b border-slate-800 px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Star className="w-5 h-5 text-white" />
          </div>
          <h1 className="font-bold text-lg tracking-tight">DigitalShop</h1>
        </div>
        <div className="bg-slate-800/50 px-3 py-1.5 rounded-full flex items-center gap-2 border border-slate-700">
          <Wallet className="w-4 h-4 text-blue-400" />
          <span className="font-mono text-sm font-medium">{userData?.balance_kzt?.toLocaleString()} ₸</span>
        </div>
      </header>

      <main className="pb-24 px-4 pt-6 max-w-lg mx-auto">
        <AnimatePresence mode="wait">
          {activeTab === 'shop' ? (
            <motion.div
              key="shop"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              <section>
                <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">Дүкен</h2>
                <div className="grid gap-3">
                  {products.map((product) => (
                    <Card key={product.id} className="flex items-center justify-between group">
                      <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-slate-900/50 text-blue-400">
                          {product.id === 'stars' && <Star className="w-6 h-6" />}
                          {product.id === 'premium' && <ShieldCheck className="w-6 h-6" />}
                          {product.id === 'nft' && <LayoutGrid className="w-6 h-6" />}
                        </div>
                        <div className="text-left">
                          <h3 className="font-semibold text-slate-100">{product.name}</h3>
                          <p className="text-xs text-slate-500">{product.price_kzt} ₸ бастап</p>
                        </div>
                      </div>
                      <button 
                        onClick={() => handleBuy(product)}
                        className="p-2 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white rounded-lg transition-all"
                      >
                        <ArrowRight className="w-5 h-5" />
                      </button>
                    </Card>
                  ))}
                </div>
              </section>

              <Card className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border-blue-500/20">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-lg text-white">Реферал жүйесі</h3>
                    <p className="text-sm text-slate-400 mt-1">Достарыңызды шақырып, 5% бонус алыңыз.</p>
                  </div>
                  <User className="w-5 h-5 text-blue-400" />
                </div>
                <Button onClick={() => tg?.openTelegramLink(`https://t.me/share/url?url=https://t.me/bot?start=${userData?.user_id}`)}>
                  Досты шақыру
                </Button>
              </Card>
            </motion.div>
          ) : activeTab === 'nft' ? (
            renderNftCatalog()
          ) : activeTab === 'profile' ? (
            <motion.div
              key="profile"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              <Card className="text-center">
                <div className="w-20 h-20 bg-slate-700 rounded-full mx-auto mb-4 flex items-center justify-center border-4 border-slate-800">
                  <User className="w-10 h-10 text-slate-400" />
                </div>
                <h2 className="text-xl font-bold text-white">@{userData?.username || 'user'}</h2>
                <p className="text-sm text-slate-500">ID: {userData?.user_id}</p>
                
                <div className="mt-6 grid grid-cols-2 gap-3">
                  <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-800">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Тапсырыстар</p>
                    <p className="text-lg font-mono font-bold text-blue-400">{userData?.orders?.length || 0}</p>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-800">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Тіл</p>
                    <p className="text-lg font-mono font-bold text-green-400">{userData?.language?.toUpperCase()}</p>
                  </div>
                </div>
              </Card>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4 px-2">Тапсырыстар тарихы</h3>
                <div className="space-y-2">
                  {userData?.orders?.map((order: any) => {
                    const isNftRental = ['gifts', 'usernames', 'numbers', 'nft'].includes(order.product_type);
                    const isExpanded = expandedOrderId === order.id;

                    return (
                      <Card 
                        key={order.id} 
                        className={cn(
                          "flex flex-col py-3 cursor-pointer transition-all duration-200",
                          isExpanded ? "bg-slate-800/50" : "hover:bg-slate-800/30"
                        )}
                        onClick={() => setExpandedOrderId(isExpanded ? null : order.id)}
                      >
                        <div className="flex justify-between items-center w-full">
                          <div>
                            <p className="font-semibold text-sm">{order.product_type}</p>
                            <p className="text-[10px] text-slate-500">{new Date(order.created_at).toLocaleDateString()}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-mono text-sm text-blue-400">{order.amount_kzt} ₸</p>
                            <p className={cn("text-[10px] uppercase font-bold", 
                              order.status === 'completed' ? "text-green-400" : 
                              (order.status === 'pending' || order.status === 'processing') ? "text-yellow-400" : 
                              (order.status === 'failed' || order.status === 'cancelled' || order.status === 'rejected') ? "text-red-400" : 
                              "text-slate-400")}>
                              {order.status}
                            </p>
                          </div>
                        </div>

                        {isExpanded && (
                          <motion.div 
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            className="mt-3 pt-3 border-t border-slate-700 w-full overflow-hidden"
                          >
                            <div className="space-y-2 text-xs">
                              {isNftRental ? (
                                <>
                                  <div className="flex justify-between">
                                    <span className="text-slate-500">Тауар атауы:</span>
                                    <span className="text-slate-200 font-medium">{order.product_name || 'NFT'}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-500">Сипаттама:</span>
                                    <span className="text-slate-200 text-right max-w-[150px]">{order.description}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-500">TON Connect:</span>
                                    <span className={cn(
                                      "font-bold",
                                      order.ton_connected ? "text-green-400" : "text-yellow-400"
                                    )}>
                                      {order.ton_connected ? "Қосылған / Подключен" : "Қосылмаған / Не подключен"}
                                    </span>
                                  </div>
                                </>
                              ) : (
                                <div className="flex justify-between">
                                  <span className="text-slate-500">Сипаттама:</span>
                                  <span className="text-slate-200">{order.description || 'Мәлімет жоқ'}</span>
                                </div>
                              )}
                              <div className="flex justify-between">
                                <span className="text-slate-500">ID:</span>
                                <span className="text-slate-400 font-mono">{order.order_id_api || order.id}</span>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </Card>
                    );
                  })}
                  {(!userData?.orders || userData.orders.length === 0) && (
                    <p className="text-center text-slate-500 py-8 text-sm italic">Тапсырыстар әлі жоқ</p>
                  )}
                </div>
              </section>
            </motion.div>
          ) : activeTab === 'admin' && userData?.is_admin ? (
            <motion.div
              key="admin"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              <h2 className="text-xl font-bold text-white mb-4">Басқару панелі</h2>
              
              <div className="grid grid-cols-2 gap-3">
                <Card className="bg-blue-600/10 border-blue-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-slate-400 uppercase">Адамдар</span>
                  </div>
                  <p className="text-2xl font-mono font-bold text-white">{adminStats?.usersCount || 0}</p>
                </Card>
                <Card className="bg-purple-600/10 border-purple-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <ShoppingCart className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-bold text-slate-400 uppercase">Тапсырыс</span>
                  </div>
                  <p className="text-2xl font-mono font-bold text-white">{adminStats?.ordersCount || 0}</p>
                </Card>
                <Card className="bg-green-600/10 border-green-500/20 col-span-2 flex justify-between items-center">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <BarChart3 className="w-4 h-4 text-green-400" />
                      <span className="text-xs font-bold text-slate-400 uppercase">Жалпы сауда / Пайда</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <p className="text-2xl font-mono font-bold text-white">{adminStats?.salesSum?.toLocaleString() || 0} ₸</p>
                      <span className="text-sm text-green-400 font-mono">+{adminStats?.profitSum?.toLocaleString() || 0} ₸</span>
                    </div>
                  </div>
                </Card>
              </div>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3 px-2">Соңғы тапсырыстар</h3>
                <div className="space-y-2">
                  {adminStats?.recentOrders?.map((order: any) => (
                    <Card key={order.id} className="flex justify-between items-center py-2">
                      <div>
                        <p className="font-semibold text-sm text-slate-200">{order.product_type}</p>
                        <p className="text-[10px] text-slate-500">ID: {order.user_id}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-sm text-blue-400">{order.amount_kzt} ₸</p>
                        <p className={cn("text-[10px] uppercase font-bold", 
                          order.status === 'completed' ? "text-green-400" : 
                          (order.status === 'pending' || order.status === 'processing') ? "text-yellow-400" : 
                          (order.status === 'failed' || order.status === 'cancelled' || order.status === 'rejected') ? "text-red-400" : 
                          "text-slate-400")}>
                          {order.status}
                        </p>
                      </div>
                    </Card>
                  ))}
                </div>
              </section>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </main>

      {/* Navigation */}
      <nav className="fixed bottom-6 left-4 right-4 z-50">
        <div className="max-w-md mx-auto bg-slate-900/90 backdrop-blur-xl border border-slate-800 p-2 rounded-2xl flex gap-2 shadow-2xl shadow-black/50">
          <button
            onClick={() => setActiveTab('shop')}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all duration-300",
              activeTab === 'shop' ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-300"
            )}
          >
            <Star className="w-5 h-5" />
            <span className="text-sm font-bold">Дүкен</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('nft');
              setView('main');
            }}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all duration-300",
              activeTab === 'nft' ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-300"
            )}
          >
            <LayoutGrid className="w-5 h-5" />
            <span className="text-sm font-bold">NFT</span>
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all duration-300",
              activeTab === 'profile' ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-300"
            )}
          >
            <User className="w-5 h-5" />
            <span className="text-sm font-bold">Профиль</span>
          </button>
          {userData?.is_admin && (
            <button
              onClick={() => setActiveTab('admin')}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all duration-300",
                activeTab === 'admin' ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-500 hover:text-slate-300"
              )}
            >
              <BarChart3 className="w-5 h-5" />
              <span className="text-sm font-bold">Админ</span>
            </button>
          )}
        </div>
      </nav>
    </div>
  );
}
