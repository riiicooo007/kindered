import React, { useMemo, useState } from "react";
import "./styles/global.css";

const people = [
  { id: 1, name: "Minh Anh", age: 22, role: "UI/UX Designer", city: "TP. Hồ Chí Minh", bio: "Thích những quán cà phê nhỏ, design và những cuộc trò chuyện không hồi kết.", tags: ["Design", "Coffee", "Photography"], image: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=700&auto=format&fit=crop&q=85", online: true, match: 96 },
  { id: 2, name: "Gia Huy", age: 24, role: "Software Engineer", city: "Thủ Đức", bio: "Code ban ngày, tìm quán ăn ngon ban đêm. Đang học chơi guitar.", tags: ["Technology", "Music", "Food"], image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=700&auto=format&fit=crop&q=85", online: true, match: 91 },
  { id: 3, name: "Thảo Vy", age: 21, role: "Content Creator", city: "Quận 3", bio: "Một chiếc người hướng ngoại, mê du lịch và kể chuyện bằng hình ảnh.", tags: ["Travel", "Movies", "Art"], image: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=700&auto=format&fit=crop&q=85", online: false, match: 89 },
  { id: 4, name: "Đức Anh", age: 23, role: "Photographer", city: "Bình Thạnh", bio: "Săn hoàng hôn, nghe indie và luôn sẵn sàng cho một chuyến đi ngẫu hứng.", tags: ["Photography", "Indie", "Travel"], image: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=700&auto=format&fit=crop&q=85", online: true, match: 87 },
];

const chats = [
  { id: 1, name: "Minh Anh", message: "Cuối tuần này đi cà phê không?", time: "2m", image: people[0].image, unread: 2 },
  { id: 2, name: "Gia Huy", message: "Haha đúng gu nhạc của mình luôn", time: "1h", image: people[1].image, unread: 0 },
  { id: 3, name: "Thảo Vy", message: "Đã gửi một bức ảnh", time: "3h", image: people[2].image, unread: 0 },
];

const navItems = [
  { id: "home", icon: "⌂", label: "Trang chủ" },
  { id: "discover", icon: "⌕", label: "Khám phá" },
  { id: "connections", icon: "♡", label: "Kết nối" },
  { id: "messages", icon: "▤", label: "Tin nhắn", count: 2 },
  { id: "communities", icon: "◎", label: "Cộng đồng" },
];

function Avatar({ src, name, size = "md", online = false }) {
  return <span className={`avatar avatar-${size}`}><img src={src} alt={name} />{online && <i className="online-dot" />}</span>;
}

function App() {
  const [active, setActive] = useState("home");
  const [liked, setLiked] = useState([2]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("Tất cả");
  const [selectedChat, setSelectedChat] = useState(chats[0]);
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState([]);
  const [toast, setToast] = useState("");

  const visiblePeople = useMemo(() => people.filter(p => {
    const matchesQuery = (p.name + p.role + p.city + p.tags.join(" ")).toLowerCase().includes(query.toLowerCase());
    const matchesFilter = filter === "Tất cả" || p.tags.includes(filter);
    return matchesQuery && matchesFilter;
  }), [query, filter]);

  const notify = (text) => { setToast(text); window.setTimeout(() => setToast(""), 2200); };
  const toggleLike = (id) => setLiked(current => current.includes(id) ? current.filter(x => x !== id) : [...current, id]);
  const sendMessage = (event) => {
    event.preventDefault();
    if (!message.trim()) return;
    setSent(current => [...current, { text: message.trim(), time: "Vừa xong" }]);
    setMessage("");
  };

  const pageTitle = ({ home: "Khám phá kết nối", discover: "Khám phá", connections: "Kết nối của bạn", messages: "Tin nhắn", communities: "Cộng đồng", profile: "Hồ sơ của bạn" })[active] || "Khám phá kết nối";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={e => { e.preventDefault(); setActive("home"); }}><span className="brand-mark">k</span><span>kindred<span className="brand-dot">.</span></span></a>
        <div className="side-label">MENU</div>
        <nav className="nav-list">
          {navItems.map(item => <button key={item.id} className={`nav-item ${active === item.id ? "active" : ""}`} onClick={() => setActive(item.id)}><span className="nav-icon">{item.icon}</span><span>{item.label}</span>{item.count && <span className="nav-count">{item.count}</span>}</button>)}
        </nav>
        <div className="side-divider" />
        <div className="side-label">KHÔNG GIAN CỦA BẠN</div>
        <button className={`nav-item ${active === "profile" ? "active" : ""}`} onClick={() => setActive("profile")}><span className="nav-icon">◉</span><span>Hồ sơ cá nhân</span></button>
        <div className="sidebar-bottom">
          <div className="mini-profile"><Avatar src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120" name="Bạn" size="sm" online /><div><strong>Alex Nguyễn</strong><small>Thành viên Kindred</small></div><button aria-label="Cài đặt" onClick={() => notify("Cài đặt sẽ sớm có mặt")}>···</button></div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumbs"><span>Kindred</span><b>/</b><strong>{pageTitle}</strong></div>
          <div className="top-actions">
            <label className="search-box"><span>⌕</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Tìm người, sở thích..." /><kbd>⌘ K</kbd></label>
            <button className="icon-button notification" aria-label="Thông báo" onClick={() => notify("Bạn đã xem hết thông báo")}>♧<i /></button>
            <Avatar src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120" name="Alex" size="sm" />
          </div>
        </header>

        <div className="content-area">
          {active === "messages" ? (
            <section className="messages-page">
              <div className="section-heading"><div><span className="eyebrow">STAY CLOSE</span><h1>Tin nhắn</h1><p>Những cuộc trò chuyện đang chờ bạn.</p></div></div>
              <div className="messages-layout">
                <div className="conversation-list"><div className="conversation-search">⌕ <span>Tìm cuộc trò chuyện</span></div>{chats.map(chat => <button key={chat.id} className={`conversation-row ${selectedChat.id === chat.id ? "selected" : ""}`} onClick={() => setSelectedChat(chat)}><Avatar src={chat.image} name={chat.name} size="md" online /><span className="conversation-meta"><strong>{chat.name}</strong><small>{chat.message}</small></span><span className="conversation-time">{chat.time}{chat.unread > 0 && <i>{chat.unread}</i>}</span></button>)}</div>
                <div className="chat-panel"><div className="chat-header"><Avatar src={selectedChat.image} name={selectedChat.name} size="sm" online /><div><strong>{selectedChat.name}</strong><small>Đang hoạt động</small></div><button className="icon-button">···</button></div><div className="chat-body"><div className="chat-date">HÔM NAY</div><div className="bubble received">Chào bạn! Mình thấy tụi mình có khá nhiều sở thích chung đó ✨<small>10:42</small></div><div className="bubble sent-bubble">Đúng rồi, rất vui được kết nối với bạn!</div>{sent.map((m, i) => <div className="bubble sent-bubble" key={i}>{m.text}<small>{m.time}</small></div>)}<div className="bubble received">{selectedChat.message}<small>10:45</small></div></div><form className="message-composer" onSubmit={sendMessage}><button type="button" aria-label="Đính kèm">＋</button><input value={message} onChange={e => setMessage(e.target.value)} placeholder="Viết tin nhắn..." /><button className="send-button" type="submit">➤</button></form></div>
              </div>
            </section>
          ) : active === "profile" ? (
            <section className="profile-page"><div className="profile-cover" /><div className="profile-details"><Avatar src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=220" name="Alex Nguyễn" size="xl" /><div><span className="eyebrow">YOUR SPACE</span><h1>Alex Nguyễn</h1><p>Thành viên từ tháng 10, 2026 · TP. Hồ Chí Minh</p></div><button className="outline-button" onClick={() => notify("Tính năng chỉnh sửa hồ sơ sẽ sớm có mặt")}>Chỉnh sửa hồ sơ</button></div><div className="profile-card"><h3>Giới thiệu</h3><p>Mình ở đây để gặp gỡ những người thú vị, chia sẻ sở thích và tạo nên những kết nối thật sự.</p><div className="tag-row"><span>Âm nhạc</span><span>Công nghệ</span><span>Du lịch</span></div></div></section>
          ) : active === "communities" ? (
            <section><div className="section-heading"><div><span className="eyebrow">FIND YOUR PEOPLE</span><h1>Cộng đồng của bạn</h1><p>Nơi những người cùng tần số gặp nhau.</p></div><button className="primary-button" onClick={() => notify("Tạo cộng đồng sẽ sớm có mặt")}>＋ Tạo cộng đồng</button></div><div className="community-grid">{[["Creative Corner","Dành cho những tâm hồn sáng tạo","2.4k thành viên","🎨"],["Coffee & Chill","Tìm bạn cà phê quanh thành phố","1.8k thành viên","☕"],["Weekend Wanderers","Hẹn nhau đi và khám phá","986 thành viên","🌿"]].map(c => <article className="community-card" key={c[0]}><div className="community-emoji">{c[3]}</div><h3>{c[0]}</h3><p>{c[1]}</p><small>{c[2]}</small><button className="outline-button" onClick={() => notify("Đã gửi yêu cầu tham gia " + c[0])}>Tham gia</button></article>)}</div></section>
          ) : (
            <>
              <section className="welcome-banner"><div className="welcome-copy"><span className="eyebrow">A LITTLE CLOSER, EVERY DAY</span><h1>Kết nối thật.<br /><em>Khoảnh khắc thật.</em></h1><p>Gặp những người cùng tần số và để những câu chuyện tự nhiên bắt đầu.</p><button className="banner-button" onClick={() => { setActive("discover"); document.getElementById("people-section")?.scrollIntoView({ behavior: "smooth" }); }}>Khám phá ngay <span>↗</span></button></div><div className="banner-art"><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" /><div className="art-circle">k<span>.</span></div><div className="floating-note note-one">✳ genuine connections</div><div className="floating-note note-two">♡ 96% match</div><div className="sparkle sparkle-one">✦</div><div className="sparkle sparkle-two">✧</div></div></section>
              <section className="stats-strip"><div><strong>2,400<span>+</span></strong><small>Thành viên mới</small></div><i /><div><strong>96<span>%</span></strong><small>Độ tương thích trung bình</small></div><i /><div><strong>320<span>+</span></strong><small>Kết nối tuần này</small></div><div className="stats-note">Mỗi kết nối là một câu chuyện mới <span>✦</span></div></section>
              <section className="people-section" id="people-section"><div className="section-heading"><div><span className="eyebrow">MADE FOR YOUR VIBE</span><h2>{active === "connections" ? "Những kết nối tiềm năng" : "Có thể bạn sẽ thích"}</h2><p>Những người có chung sở thích và năng lượng với bạn.</p></div><button className="text-link" onClick={() => setActive("discover")}>Xem tất cả <span>→</span></button></div>
                <div className="filter-row">{["Tất cả", "Design", "Coffee", "Music", "Travel", "Photography"].map(f => <button key={f} className={filter === f ? "filter-chip chosen" : "filter-chip"} onClick={() => setFilter(f)}>{f}</button>)}</div>
                <div className="people-grid">{visiblePeople.map(person => <article className="person-card" key={person.id}><div className="person-image"><img src={person.image} alt={person.name} /><span className="match-pill">{person.match}% phù hợp</span><button className={liked.includes(person.id) ? "like-button liked" : "like-button"} onClick={() => toggleLike(person.id)} aria-label="Yêu thích">{liked.includes(person.id) ? "♥" : "♡"}</button><span className={person.online ? "person-status online" : "person-status"}>{person.online ? "Đang hoạt động" : "Gần đây"}</span></div><div className="person-info"><div className="person-name"><h3>{person.name}, {person.age}</h3><span>✦</span></div><p className="person-role">{person.role} · {person.city}</p><p className="person-bio">{person.bio}</p><div className="tag-row">{person.tags.map(tag => <span key={tag}>{tag}</span>)}</div><button className="connect-button" onClick={() => { setSelectedChat({ id: person.id, name: person.name, message: "Bắt đầu cuộc trò chuyện nhé!", time: "Mới", image: person.image, unread: 0 }); setActive("messages"); }}>Gửi lời chào <span>↗</span></button></div></article>)}</div>
                {visiblePeople.length === 0 && <div className="empty-state">Không tìm thấy kết quả phù hợp. Thử từ khóa hoặc sở thích khác nhé.</div>}
              </section>
            </>
          )}
        </div>
      </main>

      <aside className="right-panel">
        <div className="right-header"><div><span className="eyebrow">YOUR CIRCLE</span><h3>Vòng kết nối</h3></div><button className="icon-button" onClick={() => setActive("messages")}>↗</button></div>
        <div className="online-summary"><div className="avatar-stack">{people.slice(0, 3).map(p => <Avatar key={p.id} src={p.image} name={p.name} size="xs" />)}</div><span><strong>12 người</strong> đang hoạt động</span></div>
        <div className="right-divider" />
        <div className="right-section-title"><strong>Tin nhắn gần đây</strong><button onClick={() => setActive("messages")}>Xem tất cả</button></div>
        <div className="recent-chats">{chats.map(chat => <button className="recent-chat" key={chat.id} onClick={() => { setSelectedChat(chat); setActive("messages"); }}><Avatar src={chat.image} name={chat.name} size="sm" online /><span className="recent-meta"><strong>{chat.name}</strong><small>{chat.message}</small></span><small className="recent-time">{chat.time}</small></button>)}</div>
        <div className="right-divider" />
        <div className="right-section-title"><strong>Gợi ý hôm nay</strong><span className="subtle-icon">✦</span></div>
        <div className="daily-prompt"><div className="prompt-icon">☀</div><span className="eyebrow">DAILY PROMPT</span><h4>Một điều nhỏ khiến bạn vui hôm nay?</h4><p>Chia sẻ câu trả lời và tìm người có cùng niềm vui với bạn.</p><button onClick={() => notify("Cảm ơn bạn đã chia sẻ!")}>Chia sẻ câu trả lời <span>→</span></button></div>
        <div className="right-footer"><span>Made for meaningful connections</span><b>kindred<span>.</span></b></div>
      </aside>
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

export default App;
