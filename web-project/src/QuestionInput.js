import React, { useEffect, useState } from 'react';
import uploadImage from './ImageService';
import tasteCatalog, { categoryOrder } from './tasteCatalog';
import { API_BASE_URL } from './config';

function QuestionInput() {
  const [catalog, setCatalog] = useState(tasteCatalog);
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState('');
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [selections, setSelections] = useState({});
  const [finalImageUrl, setFinalImageUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [userId] = useState(() => `user_${Date.now()}_${Math.random().toString(36).slice(2)}`);

  const currentCategory = categoryOrder[currentStep];
  const currentCategoryDetails = catalog[currentCategory];
  const isComplete = Boolean(finalImageUrl);
  const displayedOptions = searchResults ?? currentCategoryDetails.options;

  useEffect(() => {
    let isMounted = true;

    fetch(`${API_BASE_URL}/api/catalog`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Could not load the catalog.');
        }

        return response.json();
      })
      .then((catalogFromDatabase) => {
        if (isMounted) {
          setCatalog(catalogFromDatabase);
          setCatalogError('');
        }
      })
      .catch((loadError) => {
        if (isMounted) {
          setCatalogError(loadError.message || 'Using local fallback catalog.');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsCatalogLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    setSearchQuery('');
    setSearchResults(null);
    setSearchError('');
  }, [currentCategory]);

  const handleOptionClick = (option) => {
    setSelectedOption(option);
    setError('');
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    const query = searchQuery.trim();

    if (query.length < 2 || isSearching) {
      return;
    }

    setIsSearching(true);
    setSearchError('');
    setSelectedOption(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/search/${currentCategory}?q=${encodeURIComponent(query)}`
      );
      const body = await response.json();

      if (!response.ok) {
        throw new Error(body.error || 'Search failed.');
      }

      setSearchResults(body.options);
      if (body.options.length === 0) {
        setSearchError(`No ${currentCategoryDetails.label.toLowerCase()} results found.`);
      }
    } catch (searchRequestError) {
      setSearchResults([]);
      setSearchError(searchRequestError.message || 'Search failed.');
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
    setSearchError('');
    setSelectedOption(null);
  };

  const handleConfirm = async () => {
    if (!selectedOption || isUploading) {
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      const imageResponse = await fetch(selectedOption.imageUrl);
      if (!imageResponse.ok) {
        throw new Error('Could not load the selected image.');
      }

      const imageBlob = await imageResponse.blob();
      const imageFile = new File([imageBlob], `${selectedOption.id}.png`, { type: imageBlob.type });
      const result = await uploadImage(imageFile, currentCategory, userId);

      setSelections((currentSelections) => ({
        ...currentSelections,
        [currentCategory]: selectedOption,
      }));

      if (result.status === 'complete') {
        setFinalImageUrl(result.imageUrl);
      } else {
        setCurrentStep((step) => step + 1);
        setSelectedOption(null);
      }
    } catch (uploadError) {
      setError(uploadError.message || 'Something went wrong while saving your pick.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="taste-builder">
      <section className="builder-panel">
        <p className="eyebrow">Taste Collage</p>
        <h1>Create an image that is reprsentative of your taste and aesthetic</h1>
        <p className="intro">
          Choose a single artist, movie, and show. This app will combine all into a single image
        </p>

        <div className="step-list" aria-label="Progress">
          {categoryOrder.map((category, index) => (
            <div
              className={`step-pill ${index === currentStep ? 'active' : ''} ${selections[category] ? 'done' : ''}`}
              key={category}
            >
              {catalog[category].label}
            </div>
          ))}
        </div>

        {isCatalogLoading ? (
          <p className="status-message">Loading options from the image database...</p>
        ) : !isComplete ? (
          <>
            {catalogError && <p className="status-message">{catalogError}</p>}
            <div className="question-header">
              <span>Step {currentStep + 1} of {categoryOrder.length}</span>
              <h2>{currentCategoryDetails.prompt}</h2>
            </div>

            <form className="catalog-search" onSubmit={handleSearch}>
              <input
                aria-label={`Search ${currentCategoryDetails.label}`}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder={`Search the ${currentCategoryDetails.label.toLowerCase()} database`}
                type="search"
                value={searchQuery}
              />
              <button disabled={searchQuery.trim().length < 2 || isSearching} type="submit">
                {isSearching ? 'Searching...' : 'Search'}
              </button>
              {searchResults !== null && (
                <button className="secondary-action" onClick={clearSearch} type="button">
                  Clear
                </button>
              )}
            </form>

            {searchError && <p className="error-message">{searchError}</p>}

            <div className="option-grid">
              {displayedOptions.map((option) => (
                <button
                  className={`option-card ${selectedOption?.id === option.id ? 'selected' : ''}`}
                  key={option.id}
                  onClick={() => handleOptionClick(option)}
                  type="button"
                >
                  <img src={option.imageUrl} alt="" />
                  <strong>{option.name}</strong>
                  <span>{option.description}</span>
                  {option.provider && <small>Source: {option.provider}</small>}
                </button>
              ))}
            </div>

            {error && <p className="error-message">{error}</p>}

            <button
              className="primary-action"
              disabled={!selectedOption || isUploading}
              onClick={handleConfirm}
              type="button"
            >
              {isUploading ? 'Saving pick...' : `Confirm ${currentCategoryDetails.label}`}
            </button>
          </>
        ) : (
          <div className="result-panel">
            <h2>Your taste image is ready.</h2>
            <img src={finalImageUrl} alt="Combined taste collage" />
            <div className="selection-summary">
              {categoryOrder.map((category) => (
                <p key={category}>
                  <strong>{catalog[category].label}:</strong> {selections[category]?.name}
                </p>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}


export default QuestionInput;
