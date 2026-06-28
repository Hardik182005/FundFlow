export default function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-[#E7E9EE] p-6 ${className}`}>
      <div className="skeleton h-4 w-3/4 rounded mb-3" />
      <div className="skeleton h-8 w-1/2 rounded mb-2" />
      <div className="skeleton h-3 w-full rounded mb-2" />
      <div className="skeleton h-3 w-5/6 rounded" />
    </div>
  )
}
