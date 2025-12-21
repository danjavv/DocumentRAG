'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, FileText, DollarSign, Package, AlertCircle, Sparkles, TrendingUp } from 'lucide-react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: string
}

interface Source {
  doc_id: string
  doc_type: string
  vendor: string
  amount?: number
  date: string
  relevance: number
  excerpt: string
}

interface Stats {
  total_documents: number
  purchase_orders: number
  invoices: number
  grns: number
  total_value: number
  status: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<Stats | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Load initial data
    loadStats()
    loadSuggestions()

    // Add welcome message
    setMessages([
      {
        role: 'assistant',
        content: 'Hello! I\'m your procurement document assistant. I can help you search and analyze Purchase Orders, Invoices, and Goods Received Notes. Ask me anything!',
        timestamp: new Date().toISOString()
      }
    ])
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const loadSuggestions = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/suggestions')
      setSuggestions(response.data.suggestions)
    } catch (error) {
      console.error('Error loading suggestions:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post('http://localhost:8000/api/query', {
        question: input,
        n_results: 5
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: response.data.timestamp
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Sidebar */}
      <div className="w-80 bg-white shadow-lg p-6 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            📊 Procurement RAG
          </h1>
          <p className="text-sm text-gray-600">
            Intelligent Document Search
          </p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="space-y-4 mb-6">
            <h2 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Statistics
            </h2>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-4 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm opacity-90">Total Documents</span>
                <FileText className="w-4 h-4 opacity-75" />
              </div>
              <div className="text-3xl font-bold">{stats.total_documents}</div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                <div className="text-xs text-green-600 mb-1">Purchase Orders</div>
                <div className="text-xl font-bold text-green-700">{stats.purchase_orders}</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                <div className="text-xs text-purple-600 mb-1">Invoices</div>
                <div className="text-xl font-bold text-purple-700">{stats.invoices}</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                <div className="text-xs text-orange-600 mb-1">GRNs</div>
                <div className="text-xl font-bold text-orange-700">{stats.grns}</div>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                <div className="text-xs text-blue-600 mb-1 flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  Total Value
                </div>
                <div className="text-lg font-bold text-blue-700">
                  ${(stats.total_value / 1000).toFixed(0)}K
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Suggestions */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Quick Questions
          </h2>
          {suggestions.slice(0, 5).map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 transition-all text-sm text-gray-700 hover:text-blue-700"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm p-4 border-b border-gray-200">
          <div className="flex items-center justify-between max-w-5xl mx-auto">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Chat Assistant</h2>
              <p className="text-sm text-gray-600">Powered by Gemini 2.5 Flash</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Online</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                <div
                  className={`max-w-2xl ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm'
                      : 'bg-white text-gray-800 rounded-2xl rounded-tl-sm shadow-md'
                  } p-4`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <div className="text-sm font-semibold text-gray-600 mb-2">📚 Sources:</div>
                      {message.sources.map((source, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-50 rounded-lg p-3 text-sm border border-gray-200"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Package className="w-4 h-4 text-blue-600" />
                              <span className="font-semibold text-gray-800">{source.doc_id}</span>
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                {source.doc_type}
                              </span>
                            </div>
                            <span className="text-xs text-gray-500">
                              Relevance: {(source.relevance * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-xs text-gray-600 space-y-1">
                            <div>Vendor: {source.vendor}</div>
                            {source.amount && (
                              <div className="flex items-center gap-1">
                                <DollarSign className="w-3 h-3" />
                                Amount: ${source.amount.toLocaleString()}
                              </div>
                            )}
                            <div>Date: {source.date}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="text-xs opacity-60 mt-2">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-white text-gray-800 rounded-2xl rounded-tl-sm shadow-md p-4">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100"></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200"></div>
                    </div>
                    <span className="text-sm text-gray-600">Searching documents...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="max-w-5xl mx-auto">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about invoices, purchase orders, or GRNs..."
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
