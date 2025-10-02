import React from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useQuery } from 'react-query';
import { Search, MessageSquare, BarChart3, Clock, BookOpen, Users } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();

  const features = [
    {
      icon: <MessageSquare className="w-8 h-8 text-blue-600" />,
      title: "AI Legal Chatbot",
      description: "Ask natural language questions about Supreme Court judgments and get instant, contextual answers with proper citations.",
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-green-600" />,
      title: "Citation Analysis",
      description: "Analyze citation strength and build visual networks to understand legal precedent relationships.",
    },
    {
      icon: <Clock className="w-8 h-8 text-purple-600" />,
      title: "Timeline Extraction",
      description: "Automatically extract case timelines, key events, and legal entities from complex judgments.",
    },
    {
      icon: <BookOpen className="w-8 h-8 text-orange-600" />,
      title: "50K+ Judgments",
      description: "Access comprehensive database of Supreme Court judgments from 1950 to present day.",
    },
    {
      icon: <Search className="w-8 h-8 text-red-600" />,
      title: "Smart Search",
      description: "Find relevant cases using semantic search powered by advanced AI and vector technology.",
    },
    {
      icon: <Users className="w-8 h-8 text-indigo-600" />,
      title: "Team Collaboration",
      description: "Share research findings, save judgments, and collaborate with your legal team.",
    },
  ];

  return (
    <>
      <Head>
        <title>Veritus - AI-Powered Legal Intelligence Platform</title>
        <meta name="description" content="Transform legal research with AI-powered analysis of Supreme Court judgments" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-2xl font-bold text-gray-900">Veritus</h1>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link
                  href="/login"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              AI-Powered Legal
              <span className="text-blue-600"> Intelligence</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Transform your legal research with Veritus. Ask questions in natural language, 
              analyze citation networks, and extract insights from 50,000+ Supreme Court judgments.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => router.push('/register')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg text-lg font-semibold"
              >
                Start Free Trial
              </button>
              <button
                onClick={() => router.push('/demo')}
                className="border border-gray-300 hover:border-gray-400 text-gray-700 px-8 py-3 rounded-lg text-lg font-semibold"
              >
                View Demo
              </button>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need for Legal Research
            </h2>
            <p className="text-lg text-gray-600">
              Powerful AI tools designed specifically for legal professionals
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <div className="mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Section */}
        <div className="bg-blue-600 py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-4xl font-bold text-white mb-2">50K+</div>
                <div className="text-blue-200">Supreme Court Judgments</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-white mb-2">1950-2024</div>
                <div className="text-blue-200">Years of Legal History</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-white mb-2">1000+</div>
                <div className="text-blue-200">Legal Professionals</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-white mb-2">99.9%</div>
                <div className="text-blue-200">Uptime Guarantee</div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to Transform Your Legal Research?
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Join thousands of legal professionals who have revolutionized their research process with Veritus.
            </p>
            <button
              onClick={() => router.push('/register')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg text-lg font-semibold"
            >
              Get Started Today
            </button>
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-lg font-semibold mb-4">Veritus</h3>
                <p className="text-gray-400">
                  AI-powered legal intelligence platform for Supreme Court research.
                </p>
              </div>
              <div>
                <h4 className="text-sm font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><a href="#" className="hover:text-white">Features</a></li>
                  <li><a href="#" className="hover:text-white">Pricing</a></li>
                  <li><a href="#" className="hover:text-white">API</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold mb-4">Support</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><a href="#" className="hover:text-white">Documentation</a></li>
                  <li><a href="#" className="hover:text-white">Help Center</a></li>
                  <li><a href="#" className="hover:text-white">Contact</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold mb-4">Legal</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
                  <li><a href="#" className="hover:text-white">Terms of Service</a></li>
                  <li><a href="#" className="hover:text-white">Security</a></li>
                </ul>
              </div>
            </div>
            <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
              © 2024 Veritus. All rights reserved.
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
