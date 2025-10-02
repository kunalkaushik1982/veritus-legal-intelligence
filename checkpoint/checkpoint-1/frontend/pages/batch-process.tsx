import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Zap, Loader2, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function BatchProcess() {
  const router = useRouter();
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [batchStatus, setBatchStatus] = useState<string>('');
  const [results, setResults] = useState<any>(null);

  const processExistingPDFs = async () => {
    setIsBatchProcessing(true);
    setBatchStatus('Starting batch processing...');
    setResults(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/batch/process-existing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBatchStatus(data.message || `Processed ${data.processed || 0} of ${data.total || 0} PDFs successfully`);
        setResults(data);
        toast.success(`Batch processing completed! Processed ${data.processed || 0} PDFs`);
      } else {
        const errorData = await response.json();
        setBatchStatus(`Error: ${errorData.detail || 'Failed to process PDFs'}`);
        toast.error('Batch processing failed');
      }
    } catch (error) {
      setBatchStatus(`Error: ${error}`);
      toast.error('Batch processing failed');
      console.error('Batch processing error:', error);
    } finally {
      setIsBatchProcessing(false);
    }
  };

  return (
    <>
      <Head>
        <title>Batch Process PDFs - Veritus</title>
        <meta name="description" content="Process existing PDFs in batch" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="flex items-center text-gray-700 hover:text-gray-900 mr-4"
                >
                  <ArrowLeft className="w-5 h-5 mr-2" />
                  Back to Dashboard
                </button>
                <h1 className="text-2xl font-bold text-gray-900">Batch Process PDFs</h1>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-sm p-8">
            <div className="text-center mb-8">
              <Zap className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Process Existing PDFs
              </h2>
              <p className="text-gray-600 text-lg">
                Process all existing PDFs in your pdfs directory to extract metadata and make them available for analysis.
              </p>
            </div>

            <div className="text-center mb-8">
              <button
                onClick={processExistingPDFs}
                disabled={isBatchProcessing}
                className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-lg font-semibold rounded-xl hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {isBatchProcessing ? (
                  <>
                    <Loader2 className="w-6 h-6 mr-3 animate-spin" />
                    Processing PDFs...
                  </>
                ) : (
                  <>
                    <Zap className="w-6 h-6 mr-3" />
                    Process Existing PDFs
                  </>
                )}
              </button>
            </div>

            {batchStatus && (
              <div className="mb-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center">
                  <CheckCircle className="w-6 h-6 text-blue-600 mr-3" />
                  <p className="text-lg text-blue-800 font-medium">{batchStatus}</p>
                </div>
              </div>
            )}

            {results && results.results && (
              <div className="mt-8">
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Processing Summary</h3>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">{results.total || 0}</div>
                      <div className="text-sm text-gray-600">Total PDFs</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{results.processed || 0}</div>
                      <div className="text-sm text-gray-600">Processed</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-red-600">{results.failed || 0}</div>
                      <div className="text-sm text-gray-600">Failed</div>
                    </div>
                  </div>
                </div>

                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Processing Results ({results.results.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {results.results.map((judgment: any) => (
                    <div key={judgment.id} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{judgment.case_title || judgment.filename}</h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          judgment.extraction_status === 'success' 
                            ? 'bg-green-100 text-green-800' 
                            : judgment.extraction_status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {judgment.extraction_status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{judgment.filename}</p>
                      {judgment.summary && <p className="text-sm text-gray-500 mb-2">{judgment.summary}</p>}
                      {judgment.error && <p className="text-sm text-red-600">{judgment.error}</p>}
                      {judgment.is_processed && (
                        <button
                          onClick={() => router.push('/judgments-library')}
                          className="mt-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 text-sm"
                        >
                          View in Library
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
