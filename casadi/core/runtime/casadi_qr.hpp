// NOLINT(legal/copyright)
// SYMBOL "etree"
// Calculate the elimination tree for a matrix
// len[w] >= ata ? ncol + nrow : ncol
// len[parent] == ncol
// Ref: Chapter 4, Direct Methods for Sparse Linear Systems by Tim Davis
inline
void casadi_etree(const int* sp, int* parent, int *w, int ata) {
  int r, c, k, rnext;
  // Extract sparsity
  int nrow = *sp++, ncol = *sp++;
  const int *colind = sp, *row = sp+ncol+1;
  // Highest known ascestor of a node
  int *ancestor=w;
  // Path for A'A
  int *prev;
  if (ata) {
    prev=w+ncol;
    for (r=0; r<nrow; ++r) prev[r] = -1;
  }
  // Loop over columns
  for (c=0; c<ncol; ++c) {
    parent[c] = -1; // No parent yet
    ancestor[c] = -1; // No ancestor
    // Loop over nonzeros
    for (k=colind[c]; k<colind[c+1]; ++k) {
      r = row[k];
      if (ata) r = prev[r];
      // Traverse from r to c
      while (r!=-1 && r<c) {
        rnext = ancestor[r];
        ancestor[r] = c;
        if (rnext==-1) parent[r] = c;
        r = rnext;
      }
      if (ata) prev[row[k]] = c;
    }
  }
}

// SYMBOL "postorder_dfs"
// Traverse an elimination tree using depth first search
// Ref: Chapter 4, Direct Methods for Sparse Linear Systems by Tim Davis
inline
int casadi_postorder_dfs(int j, int k, int* head, int* next,
                         int* post, int* stack) {
  int i, p, top=0;
  stack[0] = j;
  while (top>=0) {
    p = stack[top];
    i = head[p];
    if (i==-1) {
      // No children
      top--;
      post[k++] = p;
    } else {
      // Add to stack
      head[p] = next[i];
      stack[++top] = i;
    }
  }
  return k;
}

// SYMBOL "postorder"
// Calculate the postorder permuation
// Ref: Chapter 4, Direct Methods for Sparse Linear Systems by Tim Davis
// len[w] >= 3*n
// len[post] == n
inline
void casadi_postorder(const int* parent, int n, int* post, int* w) {
  int j, k=0;
  // Work vectors
  int *head, *next, *stack;
  head=w; w+=n;
  next=w; w+=n;
  stack=w; w+=n;
  // Empty linked lists
  for (j=0; j<n; ++j) head[j] = -1;
  // Traverse nodes in reverse order
  for (j=n-1; j>=0; --j) {
    if (parent[j]!=-1) {
      next[j] = head[parent[j]];
      head[parent[j]] = j;
    }
  }
  for (j=0; j<n; j++) {
    if (parent[j]==-1) {
      k = casadi_postorder_dfs(j, k, head, next, post, stack);
    }
  }
}

// SYMBOL "leaf"
// Needed by casadi_qr_colind
// Ref: Chapter 4, Direct Methods for Sparse Linear Systems by Tim Davis
inline
int casadi_leaf(int i, int j, const int* first, int* maxfirst,
                 int* prevleaf, int* ancestor, int* jleaf) {
  int q, s, sparent, jprev;
  *jleaf = 0;
  // Quick return if j is not a leaf
  if (i<=j || first[j]<=maxfirst[i]) return -1;
  // Update max first[j] seen so far
  maxfirst[i] = first[j];
  // Previous leaf of ith subtree
  jprev = prevleaf[i];
  prevleaf[i] = j;
  // j is first or subsequent leaf
  *jleaf = (jprev == -1) ? 1 : 2;
  // if first leaf, q is root of ith subtree
  if (*jleaf==1) return i;
  // Path compression
  for (q=jprev; q!=ancestor[q]; q=ancestor[q]) {}
  for (s=jprev; s!=q; s=sparent) {
    sparent = ancestor[s];
    ancestor[s] = q;
  }
  // Return least common ancestor
  return q;
}

// SYMBOL "qr_colind"
// Calculate the row offsets for the QR R matrix
// Ref: Chapter 4, Direct Methods for Sparse Linear Systems by Tim Davis
// len[colind] = ncol+1
// len[w] >= 5*ncol + nrow + 1
// C-REPLACE "std::min" "casadi_min"
inline
void casadi_qr_colind(const int* tr_sp, const int* parent,
                      const int* post, int* l_colind, int* w) {
  int ncol = *tr_sp++, nrow = *tr_sp++;
  const int *rowind=tr_sp, *col=tr_sp+nrow+1;
  int i, j, k, J, p, q, jleaf, *maxfirst, *prevleaf,
    *ancestor, *head=0, *next=0, *first;
  // Work vectors
  ancestor=w; w+=ncol;
  maxfirst=w; w+=ncol;
  prevleaf=w; w+=ncol;
  first=w; w+=ncol;
  head=w; w+=ncol+1;
  next=w; w+=nrow;
  // Find first [j]
  for (k=0; k<ncol; ++k) first[k]=-1;
  for (k=0; k<ncol; ++k) {
    j=post[k];
    // l_colind[j]=1 if j is a leaf
    l_colind[1+j] = (first[j]==-1) ? 1 : 0;
    for (; j!=-1 && first[j]==-1; j=parent[j]) first[j]=k;
  }
  // Invert post (use ancestor as work vector)
  for (k=0; k<ncol; ++k) ancestor[post[k]] = k;
  for (k=0; k<ncol+1; ++k) head[k]=-1;
  for (i=0; i<nrow; ++i) {
    for (k=ncol, p=rowind[i]; p<rowind[i+1]; ++p) {
      k = std::min(k, ancestor[col[p]]);
    }
    // Place row i in linked list k
    next[i] = head[k];
    head[k] = i;
  }

  // Clear workspace
  for (k=0; k<ncol; ++k) maxfirst[k]=-1;
  for (k=0; k<ncol; ++k) prevleaf[k]=-1;
  // Each node in its own set
  for (i=0; i<ncol; ++i) ancestor[i]=i;
  for (k=0; k<ncol; ++k) {
    // j is the kth node in the postordered etree
    j=post[k];
    if (parent[j]!=-1) l_colind[1+parent[j]]--; // j is not a root
    J=head[k];
    while (J!=-1) { // J=j for LL' = A case
      for (p=rowind[J]; p<rowind[J+1]; ++p) {
        i=col[p];
        q = casadi_leaf(i, j, first, maxfirst, prevleaf, ancestor, &jleaf);
        if (jleaf>=1) l_colind[1+j]++; // A(i,j) is in skeleton
        if (jleaf==2) l_colind[1+q]--; // account for overlap in q
      }
      J = next[J];
    }
    if (parent[j]!=-1) ancestor[j]=parent[j];
  }
  // Sum up counts of each child
  for (j=0; j<ncol; ++j) {
    if (parent[j]!=-1) l_colind[1+parent[j]] += l_colind[1+j];
  }

  // Cumsum
  l_colind[0] = 0;
  for (j=0; j<ncol; ++j) {
    l_colind[j+1] += l_colind[j];
  }
}

// SYMBOL "qr_nnz"
// Calculate the number of nonzeros in the QR V matrix
// Ref: Chapter 5, Direct Methods for Sparse Linear Systems by Tim Davis
// len[w] >= nrow + 3*ncol
// len[pinv] == nrow + ncol
// len[leftmost] == nrow
inline
int casadi_qr_nnz(const int* sp, int* pinv, int* leftmost,
                  const int* parent, int* nrow_ext, int* w) {
  // Extract sparsity
  int nrow = sp[0], ncol = sp[1];
  const int *colind=sp+2, *row=sp+2+ncol+1;
  // Work vectors
  int *next=w; w+=nrow;
  int *head=w; w+=ncol;
  int *tail=w; w+=ncol;
  int *nque=w; w+=ncol;
  // Local variables
  int r, c, k, pa;
  // Clear queue
  for (c=0; c<ncol; ++c) head[c] = -1;
  for (c=0; c<ncol; ++c) tail[c] = -1;
  for (c=0; c<ncol; ++c) nque[c] = 0;
  for (r=0; r<nrow; ++r) leftmost[r] = -1;
  // leftmost[r] = min(find(A(r,:)))
  for (c=ncol-1; c>=0; --c) {
    for (k=colind[c]; k<colind[c+1]; ++k) {
      leftmost[row[k]] = c;
    }
  }
  // Scan rows in reverse order
  for (r=nrow-1; r>=0; --r) {
    pinv[r] = -1; // row r not yet ordered
    c=leftmost[r];

    if (c==-1) continue; // row r is empty
    if (nque[c]++ == 0) tail[c]=r; // first row in queue c
    next[r] = head[c]; // put r at head of queue c
    head[c] = r;
  }
  // Find row permutation and nnz(V)
  int v_nnz = 0;
  int nrow_new = nrow;
  for (c=0; c<ncol; ++c) {
    r = head[c]; // remove r from queue c
    v_nnz++; // count V(c,c) as nonzero
    if (r<0) r=nrow_new++; // add a fictitious row
    pinv[r] = c; // associate row r with V(:,c)
    if (--nque[c]<=0) continue; // skip if V(c+1,nrow,c) is empty
    v_nnz += nque[c]; // nque[c] is nnz(V(c+1:nrow, c))
    if ((pa=parent[c]) != -1) {
      // Move all rows to parent of c
      if (nque[pa]==0) tail[pa] = tail[c];
      next[tail[c]] = head[pa];
      head[pa] = next[r];
      nque[pa] += nque[c];
    }
  }
  for (r=0; r<nrow; ++r) if (pinv[r]<0) pinv[r] = c++;
  if (nrow_ext) *nrow_ext = nrow_new;
  return v_nnz;
}

// SYMBOL "house"
// Householder reflection
// Ref: Chapter 5, Direct Methods for Sparse Linear Systems by Tim Davis
template<typename T1>
T1 casadi_house(T1* x, T1* beta, int n) {
  // Local variable
  int i;
  // Calculate norm
  T1 x0 = x[0]; // Save x0 (overwritten below)
  T1 sigma=0;
  for (i=1; i<n; ++i) sigma += x[i]*x[i];
  T1 s = sqrt(x0*x0 + sigma); // s = norm(x)
  // Calculate consistently with symbolic datatypes (SXElem)
  T1 sigma_is_zero = sigma==0;
  T1 x0_nonpos = x0<=0;
  x[0] = if_else(sigma_is_zero, 1,
                 if_else(x0_nonpos, x0-s, -sigma/(x0+s)));
  *beta = if_else(sigma_is_zero, 2*x0_nonpos, -1/(s*x[0]));
  return s;
}

// SYMBOL "happly"
// Apply householder reflection
// Ref: Chapter 5, Direct Methods for Sparse Linear Systems by Tim Davis
template<typename T1>
void casadi_happly(const int* sp_v, const T1* v, int i, T1 beta, T1* x) {
  // Extract sparsity
  int nrow=sp_v[0], ncol=sp_v[1];
  const int *colind=sp_v+2, *row=sp_v+2+ncol+1;
  // Local variables
  int k;
  // tau = v'*x
  T1 tau=0;
  for (k=colind[i]; k<colind[i+1]; ++k) tau += v[k] * x[row[k]];
  // tau = beta*v'*x
  tau *= beta;
  // x -= v*tau
  for (k=colind[i]; k<colind[i+1]; ++k) x[row[k]] -= v[k]*tau;
}

// SYMBOL "qr"
// Apply householder reflection
// Ref: Chapter 5, Direct Methods for Sparse Linear Systems by Tim Davis
// Note: nrow <= nrow_ext <= ncol
// len[iw] = nrow_ext + ncol
// len[x] = nrow_ext
// sp_v = [nrow_ext, ncol, 0, 0, ...] len[3 + ncol + nnz_v]
// len[v] nnz_v
// sp_r = [nrow_ext, ncol, 0, 0, ...] len[3 + ncol + nnz_r]
// len[r] nnz_r
// len[beta] ncol
template<typename T1>
void casadi_qr(const int* sp_a, const T1* nz_a, int* iw, T1* x,
               int* sp_v, T1* nz_v, int* sp_r, T1* nz_r, T1* beta,
               const int* leftmost, const int* parent, const int* pinv) {
  // Extract sparsities
  int nrow = sp_a[0], ncol = sp_a[1];
  const int *colind=sp_a+2, *row=sp_a+2+ncol+1;
  int nrow_ext = sp_v[0];
  int *v_colind=sp_v+2, *v_row=sp_v+2+ncol+1;
  int *r_colind=sp_r+2, *r_row=sp_r+2+ncol+1;
  // Work vectors
  int* s = iw; iw += ncol;
  // Local variables
  int r, c, k, k1, top, len, k2, r2;
  // Clear workspace x
  for (r=0; r<nrow_ext; ++r) x[r] = 0;
  // Clear w to mark nodes
  for (r=0; r<nrow_ext; ++r) iw[r] = -1;
  // Number of nonzeros in v and r
  int nnz_r=0, nnz_v=0;
  // Compute V and R
  for (c=0; c<ncol; ++c) {
    // R(:,c) starts here
    r_colind[c] = nnz_r;
    // V(:, c) starts here
    v_colind[c] = k1 = nnz_v;
    // Add V(c,c) to pattern of V
    iw[c] = c;
    v_row[nnz_v++] = c;
    top = ncol;
    for (k=colind[c]; k<colind[c+1]; ++k) {
      r = leftmost[row[k]]; // r = min(find(A(r,:))
      // Traverse up c
      for (len=0; iw[r]!=c; r=parent[r]) {
        s[len++] = r;
        iw[r] = c;
      }
      while (len>0) s[--top] = s[--len]; // push path on stack
      r = pinv[row[k]]; // r = permuted row of A(:,c)
      x[r] = nz_a[k]; // x(r) = A(:,c)
      if (r>c && iw[r]<c) {
        v_row[nnz_v++] = r; // add r to pattern of V(:,c)
        iw[r] = c;
      }
    }
    // For each r in pattern of R(:,c)
    for (k = top; k<ncol; ++k) {
      // R(r,c) is nonzero
      r = s[k];
      // Apply (V(r), beta(r)) to x
      casadi_happly(sp_v, nz_v, r, beta[r], x);
      r_row[nnz_r] = r;
      nz_r[nnz_r++] = x[r];
      x[r] = 0;
      if (parent[r]==c) {
        for (k2=v_colind[r]; k2<v_colind[r+1]; ++k2) {
          r2 = v_row[k2];
          if (iw[r2]<c) {
            iw[r2] = c;
            v_row[nnz_v++] = r2;
          }
        }
      }
    }
    // Gather V(:,c) = x
    for (k=k1; k<nnz_v; ++k) {
      nz_v[k] = x[v_row[k]];
      x[v_row[k]] = 0;
    }
    // R(c,c) = norm(x)
    r_row[nnz_r] = c;
    nz_r[nnz_r++] = casadi_house(nz_v + k1, beta + c, nnz_v-k1);
  }
  // Finalize R, V
  r_colind[ncol] = nnz_r;
  v_colind[ncol] = nnz_v;
}