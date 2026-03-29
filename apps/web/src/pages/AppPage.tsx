import { SignedIn, SignedOut, UserButton, useAuth, useUser } from "@clerk/clerk-react";
import { FormEvent, useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

const clerkPublishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const clerkJwtTemplate = import.meta.env.VITE_CLERK_JWT_TEMPLATE;
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

type Organization = {
  organization_id: string;
  organization_name: string;
  industry?: string;
  role?: string;
};

type Workspace = {
  workspace_id: string;
  organization_id: string;
  workspace_name: string;
  workspace_slug: string;
  description: string;
  purpose: string;
  workspace_type: string;
};

type Member = {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
  workspace_ids: string[];
};

type DocumentRecord = {
  document_id: string;
  source: string;
  source_type: string;
  ingestion_status: string;
  chunk_count: number;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type NavSection = "dashboard" | "organizations" | "workspaces";
type WorkspacePanel = "overview" | "ingest" | "chat" | "members";

const api = async <T,>(path: string, token: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${await response.text()}`);
  }

  return response.json() as Promise<T>;
};

export default function AppPage() {
  if (!clerkPublishableKey) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="auth-kicker">Clerk Setup Required</p>
          <h1>App access is waiting on Clerk configuration</h1>
          <p className="auth-copy">
            Set <code>VITE_CLERK_PUBLISHABLE_KEY</code> in the root environment and configure the
            backend with Clerk JWT settings before using authenticated app routes.
          </p>
          <Link to="/" className="auth-link">
            Back to landing page
          </Link>
        </section>
      </main>
    );
  }

  return (
    <>
      <SignedIn>
        <AuthenticatedApp />
      </SignedIn>
      <SignedOut>
        <Navigate to="/sign-in" replace />
      </SignedOut>
    </>
  );
}

function AuthenticatedApp() {
  const { isLoaded, getToken } = useAuth();
  const { user } = useUser();
  const navigate = useNavigate();
  const location = useLocation();

  const workspaceRouteId = location.pathname.startsWith("/app/workspaces/")
    ? decodeURIComponent(location.pathname.replace("/app/workspaces/", ""))
    : "";

  const [authStatus, setAuthStatus] = useState("Initializing Clerk session…");
  const [error, setError] = useState<string | null>(null);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [workspaceMembers, setWorkspaceMembers] = useState<Member[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loadingWorkspaceData, setLoadingWorkspaceData] = useState(false);
  const [workspacePanel, setWorkspacePanel] = useState<WorkspacePanel>("overview");

  const [orgName, setOrgName] = useState("");
  const [orgIndustry, setOrgIndustry] = useState("facilities");
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDescription, setWorkspaceDescription] = useState("");
  const [workspacePurpose, setWorkspacePurpose] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviteWorkspaceIds, setInviteWorkspaceIds] = useState<string[]>([]);

  const [ingestNamespace, setIngestNamespace] = useState("aurora");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadSourcePath, setUploadSourcePath] = useState("");
  const [uploadSourceUrl, setUploadSourceUrl] = useState("");

  const [chatDraft, setChatDraft] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [sources, setSources] = useState<Array<{ source: string; snippet: string }>>([]);

  useEffect(() => {
    if (!workspaceRouteId) return;
    const orgPrefix = workspaceRouteId.split("::")[0] ?? "";
    if (orgPrefix && orgPrefix !== selectedOrgId) {
      setSelectedOrgId(orgPrefix);
    }
  }, [workspaceRouteId, selectedOrgId]);

  useEffect(() => {
    let cancelled = false;

    if (!isLoaded) {
      return () => {
        cancelled = true;
      };
    }

    (async () => {
      try {
        const tokenInfo = await getFreshToken(getToken);
        const orgResponse = await api<{ organizations: Organization[] }>("/me/organizations", tokenInfo.token);

        if (!cancelled) {
          setOrganizations(orgResponse.organizations);
          setSelectedOrgId((current) => current || workspaceRouteId.split("::")[0] || orgResponse.organizations[0]?.organization_id || "");
          setAuthStatus(`Using ${tokenInfo.label}.`);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setAuthStatus("Clerk sign-in succeeded, but backend auth is not fully connected yet.");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getToken, isLoaded, workspaceRouteId]);

  useEffect(() => {
    let cancelled = false;

    if (!isLoaded || !selectedOrgId) {
      setWorkspaces([]);
      setMembers([]);
      return () => {
        cancelled = true;
      };
    }

    setLoadingWorkspaceData(true);

    (async () => {
      try {
        const tokenInfo = await getFreshToken(getToken);
        if (!cancelled) {
          setAuthStatus(`Using ${tokenInfo.label}.`);
        }
        const [workspaceResponse, membersResponse] = await Promise.all([
          api<{ workspaces: Workspace[] }>(
            `/me/workspaces?organizationId=${encodeURIComponent(selectedOrgId)}`,
            tokenInfo.token
          ),
          api<{ members: Member[] }>(`/organizations/${selectedOrgId}/members`, tokenInfo.token).catch(() => ({ members: [] })),
        ]);

        if (!cancelled) {
          setWorkspaces(workspaceResponse.workspaces);
          setMembers(membersResponse.members);
          if (inviteRole === "member" && !inviteWorkspaceIds.length && workspaceResponse.workspaces.length) {
            setInviteWorkspaceIds([workspaceResponse.workspaces[0].workspace_id]);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setLoadingWorkspaceData(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getToken, inviteRole, inviteWorkspaceIds.length, isLoaded, selectedOrgId]);

  useEffect(() => {
    let cancelled = false;

    if (!isLoaded || !workspaceRouteId) {
      setDocuments([]);
      setWorkspaceMembers([]);
      setChatMessages([]);
      setSources([]);
      return () => {
        cancelled = true;
      };
    }

    (async () => {
      try {
        const tokenInfo = await getFreshToken(getToken);
        if (!cancelled) {
          setAuthStatus(`Using ${tokenInfo.label}.`);
        }
        const [documentsResponse, membersResponse] = await Promise.all([
          api<{ documents: DocumentRecord[] }>(`/workspaces/${workspaceRouteId}/documents`, tokenInfo.token),
          api<{ members: Member[] }>(`/organizations/workspaces/${workspaceRouteId}/members`, tokenInfo.token),
        ]);

        if (!cancelled) {
          setDocuments(documentsResponse.documents);
          setWorkspaceMembers(membersResponse.members);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getToken, isLoaded, workspaceRouteId]);

  if (!isLoaded) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="auth-kicker">Clerk Authentication</p>
          <h1>Loading your secure session</h1>
          <p className="auth-copy">Waiting for Clerk to finish loading before calling the API.</p>
        </section>
      </main>
    );
  }

  const currentSection: NavSection = workspaceRouteId
    ? "workspaces"
    : location.pathname === "/app/organizations"
      ? "organizations"
      : location.pathname === "/app/workspaces"
        ? "workspaces"
        : "dashboard";

  const selectedOrg = organizations.find((organization) => organization.organization_id === selectedOrgId) || null;
  const selectedWorkspace = workspaces.find((workspace) => workspace.workspace_id === workspaceRouteId) || null;
  const orgAdmins = members.filter((member) => member.role === "owner" || member.role === "admin").length;
  const workspaceDocumentCount = documents.length;
  const workspaceMemberCount = workspaceMembers.length;
  const pageMeta = workspaceRouteId
    ? {
        kicker: "Workspace",
        title: selectedWorkspace?.workspace_name ?? "Workspace detail",
        description:
          selectedWorkspace?.description ||
          selectedWorkspace?.purpose ||
          "Review knowledge sources, launch chat, and manage workspace access from one place.",
      }
    : currentSection === "organizations"
      ? {
          kicker: "Organization",
          title: selectedOrg?.organization_name ?? "Organization management",
          description:
            "See organization detail, browse available workspaces, and manage members without leaving the current tenant.",
        }
      : currentSection === "workspaces"
        ? {
            kicker: "Workspaces",
            title: selectedOrg ? `${selectedOrg.organization_name} workspaces` : "Workspace library",
            description:
              "Open any workspace to view its details, launch chat, or manage the knowledge sources behind it.",
          }
        : {
            kicker: "Dashboard",
            title: "Platform overview",
            description:
              "Start with the organizations you manage, then move into workspace operations only when you need to.",
          };

  const refreshOrganizations = async () => {
    const tokenInfo = await getFreshToken(getToken);
    setAuthStatus(`Using ${tokenInfo.label}.`);
    const orgResponse = await api<{ organizations: Organization[] }>("/me/organizations", tokenInfo.token);
    setOrganizations(orgResponse.organizations);
    setSelectedOrgId((current) => current || orgResponse.organizations[0]?.organization_id || "");
  };

  const refreshOrgData = async () => {
    if (!selectedOrgId) return;
    const tokenInfo = await getFreshToken(getToken);
    setAuthStatus(`Using ${tokenInfo.label}.`);
    const [workspaceResponse, membersResponse] = await Promise.all([
      api<{ workspaces: Workspace[] }>(
        `/me/workspaces?organizationId=${encodeURIComponent(selectedOrgId)}`,
        tokenInfo.token
      ),
      api<{ members: Member[] }>(`/organizations/${selectedOrgId}/members`, tokenInfo.token),
    ]);
    setWorkspaces(workspaceResponse.workspaces);
    setMembers(membersResponse.members);
  };

  const refreshWorkspaceArtifacts = async (workspaceId: string) => {
    const tokenInfo = await getFreshToken(getToken);
    setAuthStatus(`Using ${tokenInfo.label}.`);
    const [documentsResponse, membersResponse] = await Promise.all([
      api<{ documents: DocumentRecord[] }>(`/workspaces/${workspaceId}/documents`, tokenInfo.token),
      api<{ members: Member[] }>(`/organizations/workspaces/${workspaceId}/members`, tokenInfo.token),
    ]);
    setDocuments(documentsResponse.documents);
    setWorkspaceMembers(membersResponse.members);
  };

  const handleNav = (section: NavSection) => {
    if (section === "dashboard") navigate("/app");
    if (section === "organizations") navigate("/app/organizations");
    if (section === "workspaces") navigate("/app/workspaces");
  };

  const handleOrgChange = (organizationId: string) => {
    setSelectedOrgId(organizationId);
    if (workspaceRouteId) {
      navigate("/app/workspaces");
    }
  };

  const handleCreateOrganization = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const tokenInfo = await getFreshToken(getToken);
      setAuthStatus(`Using ${tokenInfo.label}.`);
      const response = await api<{ organization: { organization_id: string } }>(
        "/organizations",
        tokenInfo.token,
        {
          method: "POST",
          body: JSON.stringify({
            organization_name: orgName,
            industry: orgIndustry,
          }),
        }
      );
      setOrgName("");
      await refreshOrganizations();
      setSelectedOrgId(response.organization.organization_id);
      navigate("/app/organizations");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleCreateWorkspace = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedOrgId) return;
    try {
      const tokenInfo = await getFreshToken(getToken);
      setAuthStatus(`Using ${tokenInfo.label}.`);
      const response = await api<{ workspace: Workspace }>(
        `/organizations/${selectedOrgId}/workspaces`,
        tokenInfo.token,
        {
          method: "POST",
          body: JSON.stringify({
            workspace_name: workspaceName,
            description: workspaceDescription,
            purpose: workspacePurpose,
            workspace_type: "knowledge",
          }),
        }
      );
      setWorkspaceName("");
      setWorkspaceDescription("");
      setWorkspacePurpose("");
      await refreshOrgData();
      navigate(`/app/workspaces/${encodeURIComponent(response.workspace.workspace_id)}`);
      setWorkspacePanel("overview");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleInviteMember = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedOrgId) return;
    try {
      const tokenInfo = await getFreshToken(getToken);
      setAuthStatus(`Using ${tokenInfo.label}.`);
      await api<{ member: Member }>(`/organizations/${selectedOrgId}/members/invite`, tokenInfo.token, {
        method: "POST",
        body: JSON.stringify({
          email: inviteEmail,
          display_name: inviteName || undefined,
          role: inviteRole,
          workspace_ids: inviteRole === "member" ? inviteWorkspaceIds : [],
        }),
      });
      setInviteEmail("");
      setInviteName("");
      setInviteRole("member");
      setInviteWorkspaceIds([]);
      await refreshOrgData();
      if (workspaceRouteId) {
        await refreshWorkspaceArtifacts(workspaceRouteId);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleUploadFile = async (event: FormEvent) => {
    event.preventDefault();
    if (!workspaceRouteId || !uploadFile) return;
    try {
      const tokenInfo = await getFreshToken(getToken);
      setAuthStatus(`Using ${tokenInfo.label}.`);
      const formData = new FormData();
      formData.append("namespace", ingestNamespace);
      formData.append("file", uploadFile);
      const response = await fetch(`${apiBaseUrl}/workspaces/${workspaceRouteId}/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${tokenInfo.token}`,
        },
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`${response.status} ${await response.text()}`);
      }
      setUploadFile(null);
      await refreshWorkspaceArtifacts(workspaceRouteId);
      setWorkspacePanel("ingest");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleQueueSource = async (event: FormEvent, source: string, sourceType: "url" | "file") => {
    event.preventDefault();
    if (!workspaceRouteId || !source.trim()) return;
    try {
      const tokenInfo = await getFreshToken(getToken);
      setAuthStatus(`Using ${tokenInfo.label}.`);
      await api<{ job_id: string }>(`/workspaces/${workspaceRouteId}/ingest`, tokenInfo.token, {
        method: "POST",
        body: JSON.stringify({
          namespace: ingestNamespace,
          source,
          source_type: sourceType,
        }),
      });
      if (sourceType === "url") setUploadSourceUrl("");
      if (sourceType === "file") setUploadSourcePath("");
      await refreshWorkspaceArtifacts(workspaceRouteId);
      setWorkspacePanel("ingest");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleChat = async (event: FormEvent) => {
    event.preventDefault();
    if (!workspaceRouteId || !chatDraft.trim()) return;
    const nextMessages: ChatMessage[] = [...chatMessages, { role: "user", content: chatDraft.trim() }];
    setChatMessages(nextMessages);
    setChatDraft("");

    try {
      const tokenInfo = await getFreshToken(getToken);
      setAuthStatus(`Using ${tokenInfo.label}.`);
      const response = await api<{ reply: string; sources: Array<{ source: string; snippet: string }> }>(
        `/workspaces/${workspaceRouteId}/chat`,
        tokenInfo.token,
        {
          method: "POST",
          body: JSON.stringify({ messages: nextMessages }),
        }
      );
      setChatMessages([...nextMessages, { role: "assistant", content: response.reply }]);
      setSources(response.sources);
      setWorkspacePanel("chat");
      setError(null);
    } catch (err) {
      setChatMessages(nextMessages);
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const renderWorkspaceCards = (emptyMessage: string) => {
    if (!selectedOrg) {
      return <p className="muted-copy">{emptyMessage}</p>;
    }

    return (
      <div className="workspace-tile-grid">
        {loadingWorkspaceData ? <p className="muted-copy">Loading workspaces…</p> : null}
        {workspaces.map((workspace) => (
          <button
            key={workspace.workspace_id}
            type="button"
            className="workspace-tile"
            onClick={() => navigate(`/app/workspaces/${encodeURIComponent(workspace.workspace_id)}`)}
          >
            <div className="workspace-tile-topline">
              <span className="workspace-tile-badge">{workspace.workspace_type}</span>
              <span className="workspace-tile-slug">{workspace.workspace_slug}</span>
            </div>
            <strong>{workspace.workspace_name}</strong>
            <p>{workspace.description || workspace.purpose || "Workspace ready for knowledge sources and chat."}</p>
            <small>Open workspace detail</small>
          </button>
        ))}
        {!workspaces.length ? <p className="muted-copy">No visible workspaces yet.</p> : null}
      </div>
    );
  };

  return (
    <main className="enterprise-shell">
      <aside className="enterprise-sidebar">
        <div className="sidebar-brand">
          <p className="auth-kicker">AI Knowledge Assistant</p>
          <h1>Platform Admin</h1>
          <p className="muted-copy compact-copy">
            A simpler control center for organizations, knowledge workspaces, and trusted answers.
          </p>
        </div>

        <nav className="sidebar-nav">
          <button
            type="button"
            className={currentSection === "dashboard" ? "sidebar-link sidebar-link-active" : "sidebar-link"}
            onClick={() => handleNav("dashboard")}
          >
            <span>Dashboard</span>
            <small>Overview</small>
          </button>
          <button
            type="button"
            className={currentSection === "organizations" ? "sidebar-link sidebar-link-active" : "sidebar-link"}
            onClick={() => handleNav("organizations")}
          >
            <span>Organizations</span>
            <small>Tenant admin</small>
          </button>
          <button
            type="button"
            className={currentSection === "workspaces" ? "sidebar-link sidebar-link-active" : "sidebar-link"}
            onClick={() => handleNav("workspaces")}
          >
            <span>Workspaces</span>
            <small>Knowledge operations</small>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-context">
            <span className="sidebar-context-label">Current organization</span>
            <strong>{selectedOrg?.organization_name ?? "No organization selected"}</strong>
            <small>{selectedOrg?.industry ?? "Choose an organization to continue"}</small>
          </div>
        </div>
      </aside>

      <section className="enterprise-main">
        <header className="topbar">
          <div className="page-hero">
            <p className="auth-kicker">{pageMeta.kicker}</p>
            <h2>{pageMeta.title}</h2>
            <p className="muted-copy">{pageMeta.description}</p>
          </div>
          <div className="topbar-controls">
            <label className="org-switcher">
              <span className="org-switcher-label">Organization</span>
              <select
                className="topbar-select"
                value={selectedOrgId}
                onChange={(event) => handleOrgChange(event.target.value)}
              >
                <option value="">Select organization</option>
                {organizations.map((organization) => (
                  <option key={organization.organization_id} value={organization.organization_id}>
                    {organization.organization_name}
                  </option>
                ))}
              </select>
            </label>
            <div className="account-chip">
              <div className="account-chip-copy">
                <span className="account-chip-label">Manage account</span>
                <strong>{user?.primaryEmailAddress?.emailAddress ?? user?.username ?? "Unknown"}</strong>
                <small>{authStatus}</small>
              </div>
              <UserButton afterSignOutUrl="/" />
            </div>
            <Link to="/" className="auth-link">
              Landing page
            </Link>
          </div>
        </header>

        {error && (
          <div className="auth-note error-note">
            <strong>Action required:</strong> {error}
          </div>
        )}

        {!workspaceRouteId ? (
          <>
            <div className="summary-strip">
              <div className="summary-card">
                <span className="summary-label">Organizations</span>
                <strong className="summary-value">{organizations.length}</strong>
                <small>Tenants visible to this user</small>
              </div>
              <div className="summary-card">
                <span className="summary-label">Visible workspaces</span>
                <strong className="summary-value">{workspaces.length}</strong>
                <small>Within the selected organization</small>
              </div>
              <div className="summary-card">
                <span className="summary-label">Org admins</span>
                <strong className="summary-value">{orgAdmins}</strong>
                <small>Owners and admins with full org visibility</small>
              </div>
              <div className="summary-card">
                <span className="summary-label">Signed in user</span>
                <strong className="summary-value summary-value-small">
                  {user?.primaryEmailAddress?.emailAddress ?? user?.username ?? "Unknown"}
                </strong>
                <small>Managed with Clerk</small>
              </div>
            </div>

            {currentSection === "dashboard" ? (
              <section className="enterprise-section">
                <div className="page-layout">
                  <div className="page-main">
                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Selected organization</p>
                          <h3>Start from the organization you want to manage</h3>
                        </div>
                      </div>
                      {selectedOrg ? (
                        <div className="detail-stack">
                          <div className="detail-card detail-card-emphasis">
                            <strong>{selectedOrg.organization_name}</strong>
                            <span>{selectedOrg.industry ?? "industry not set"}</span>
                            <small>{selectedOrg.role ?? "member"} access</small>
                          </div>
                          <div className="detail-grid">
                            <div className="detail-card">
                              <strong>Workspace footprint</strong>
                              <span>{workspaces.length} available workspaces</span>
                              <small>Open any workspace to review documents, chat, or access</small>
                            </div>
                            <div className="detail-card">
                              <strong>Organization admins</strong>
                              <span>{orgAdmins}</span>
                              <small>Admins and owners inherit all workspaces</small>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="muted-copy">Select an organization from the top bar to see its current state.</p>
                      )}
                    </section>

                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Available workspaces</p>
                          <h3>Open the workspace your team needs</h3>
                        </div>
                      </div>
                      {renderWorkspaceCards("Select an organization to view its workspaces.")}
                    </section>
                  </div>

                  <aside className="page-side">
                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Quick action</p>
                          <h3>Create organization</h3>
                        </div>
                      </div>
                      <p className="muted-copy compact-copy">
                        Use this from the dashboard only, so the rest of the product stays focused on the selected organization.
                      </p>
                      <form className="stack-form" onSubmit={handleCreateOrganization}>
                        <input value={orgName} onChange={(event) => setOrgName(event.target.value)} placeholder="Organization name" />
                        <input value={orgIndustry} onChange={(event) => setOrgIndustry(event.target.value)} placeholder="Industry" />
                        <button type="submit">Create organization</button>
                      </form>
                    </section>

                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Recommended flow</p>
                          <h3>How most teams move through the app</h3>
                        </div>
                      </div>
                      <div className="step-list">
                        <div className="step-item">
                          <span>1</span>
                          <p>Create or choose an organization from the dashboard.</p>
                        </div>
                        <div className="step-item">
                          <span>2</span>
                          <p>Use the organization page to create workspaces and invite members.</p>
                        </div>
                        <div className="step-item">
                          <span>3</span>
                          <p>Open a workspace to add knowledge, launch chat, and review access.</p>
                        </div>
                      </div>
                    </section>
                  </aside>
                </div>
              </section>
            ) : null}

            {currentSection === "organizations" ? (
              <section className="enterprise-section">
                <div className="page-layout">
                  <div className="page-main">
                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Organization detail</p>
                          <h3>See the tenant context before changing anything</h3>
                        </div>
                      </div>
                      {selectedOrg ? (
                        <div className="detail-stack">
                          <div className="detail-card detail-card-emphasis">
                            <strong>{selectedOrg.organization_name}</strong>
                            <span>{selectedOrg.industry ?? "industry not set"}</span>
                            <small>{selectedOrg.role ?? "member"} access</small>
                          </div>
                          <div className="detail-grid">
                            <div className="detail-card">
                              <strong>Members</strong>
                              <span>{members.length}</span>
                              <small>Organization users with some level of access</small>
                            </div>
                            <div className="detail-card">
                              <strong>Available workspaces</strong>
                              <span>{workspaces.length}</span>
                              <small>Workspace cards below open each workspace detail page</small>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="muted-copy">Select an organization to view its detail.</p>
                      )}
                    </section>

                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Workspaces</p>
                          <h3>Available workspaces in this organization</h3>
                        </div>
                      </div>
                      {renderWorkspaceCards("Select an organization to view its workspaces.")}
                    </section>

                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Members</p>
                          <h3>Organization members</h3>
                        </div>
                      </div>
                      {selectedOrg ? (
                        <div className="list-panel">
                          {members.map((member) => (
                            <div key={member.user_id} className="member-row">
                              <div>
                                <strong>{member.display_name || member.email}</strong>
                                <span>{member.email}</span>
                              </div>
                              <small>
                                {member.role} · {member.workspace_ids.length ? `${member.workspace_ids.length} assigned workspaces` : "all workspaces"}
                              </small>
                            </div>
                          ))}
                          {!members.length ? <p className="muted-copy">No member records available.</p> : null}
                        </div>
                      ) : (
                        <p className="muted-copy">Select an organization to view member details.</p>
                      )}
                    </section>
                  </div>

                  <aside className="page-side">
                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Create workspace</p>
                          <h3>Add a new workspace</h3>
                        </div>
                      </div>
                      {selectedOrg ? (
                        <form className="stack-form" onSubmit={handleCreateWorkspace}>
                          <input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} placeholder="Workspace name" />
                          <input
                            value={workspaceDescription}
                            onChange={(event) => setWorkspaceDescription(event.target.value)}
                            placeholder="General description"
                          />
                          <input value={workspacePurpose} onChange={(event) => setWorkspacePurpose(event.target.value)} placeholder="Purpose" />
                          <button type="submit">Create workspace</button>
                        </form>
                      ) : (
                        <p className="muted-copy">Select an organization before creating workspaces.</p>
                      )}
                    </section>

                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Invite member</p>
                          <h3>Grant organization or workspace access</h3>
                        </div>
                      </div>
                      {selectedOrg ? (
                        <>
                          <form className="stack-form" onSubmit={handleInviteMember}>
                            <input value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="Member email" />
                            <input value={inviteName} onChange={(event) => setInviteName(event.target.value)} placeholder="Display name (optional)" />
                            <select value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>
                              <option value="member">Member</option>
                              <option value="admin">Admin</option>
                              <option value="owner">Owner</option>
                            </select>
                            {inviteRole === "member" ? (
                              <div className="checkbox-list">
                                {workspaces.map((workspace) => (
                                  <label key={workspace.workspace_id}>
                                    <input
                                      type="checkbox"
                                      checked={inviteWorkspaceIds.includes(workspace.workspace_id)}
                                      onChange={(event) =>
                                        setInviteWorkspaceIds((current) =>
                                          event.target.checked
                                            ? [...current, workspace.workspace_id]
                                            : current.filter((workspaceId) => workspaceId !== workspace.workspace_id)
                                        )
                                      }
                                    />
                                    <span>{workspace.workspace_name}</span>
                                  </label>
                                ))}
                              </div>
                            ) : null}
                            <button type="submit">Invite member</button>
                          </form>
                          <p className="muted-copy compact-copy">
                            Members can be limited to specific workspaces. Admins and owners inherit full organization visibility.
                          </p>
                        </>
                      ) : (
                        <p className="muted-copy">Select an organization before inviting members.</p>
                      )}
                    </section>
                  </aside>
                </div>
              </section>
            ) : null}

            {currentSection === "workspaces" ? (
              <section className="enterprise-section">
                <div className="page-layout">
                  <div className="page-main">
                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Workspace library</p>
                          <h3>Choose a workspace to continue</h3>
                        </div>
                      </div>
                      {renderWorkspaceCards("Select an organization to view its workspaces.")}
                    </section>
                  </div>

                  <aside className="page-side">
                    <section className="console-panel">
                      <div className="panel-heading">
                        <div>
                          <p className="auth-kicker">Current organization</p>
                          <h3>Context</h3>
                        </div>
                      </div>
                      {selectedOrg ? (
                        <div className="detail-stack">
                          <div className="detail-card detail-card-emphasis">
                            <strong>{selectedOrg.organization_name}</strong>
                            <span>{selectedOrg.industry ?? "industry not set"}</span>
                            <small>{selectedOrg.role ?? "member"} access</small>
                          </div>
                          <div className="detail-card">
                            <strong>Workspaces</strong>
                            <span>{workspaces.length}</span>
                            <small>Open one to manage knowledge, chat, and members</small>
                          </div>
                        </div>
                      ) : (
                        <p className="muted-copy">Select an organization to view its workspace library.</p>
                      )}
                    </section>
                  </aside>
                </div>
              </section>
            ) : null}
          </>
        ) : (
          <section className="enterprise-section">
            <div className="workspace-header">
              <div className="workspace-header-copy">
                <button type="button" className="ghost-button" onClick={() => navigate("/app/workspaces")}>
                  Back to workspaces
                </button>
                <div>
                  <p className="auth-kicker">Workspace detail</p>
                  <h3>{selectedWorkspace?.workspace_name ?? "Workspace"}</h3>
                  <p className="muted-copy">
                    {selectedWorkspace?.description || selectedWorkspace?.purpose || "Manage ingestion, chat, and workspace access from this workbench."}
                  </p>
                </div>
              </div>
              <div className="workspace-overview-chips">
                <div className="summary-chip">
                  <span>Documents</span>
                  <strong>{workspaceDocumentCount}</strong>
                </div>
                <div className="summary-chip">
                  <span>Members</span>
                  <strong>{workspaceMemberCount}</strong>
                </div>
              </div>
            </div>

            <div className="workspace-tabs">
              <button
                type="button"
                className={workspacePanel === "overview" ? "tab-button tab-button-active" : "tab-button"}
                onClick={() => setWorkspacePanel("overview")}
              >
                Overview
              </button>
              <button
                type="button"
                className={workspacePanel === "ingest" ? "tab-button tab-button-active" : "tab-button"}
                onClick={() => setWorkspacePanel("ingest")}
              >
                Knowledge intake
              </button>
              <button
                type="button"
                className={workspacePanel === "chat" ? "tab-button tab-button-active" : "tab-button"}
                onClick={() => setWorkspacePanel("chat")}
              >
                Chat
              </button>
              <button
                type="button"
                className={workspacePanel === "members" ? "tab-button tab-button-active" : "tab-button"}
                onClick={() => setWorkspacePanel("members")}
              >
                Members
              </button>
            </div>

            <div className="workspace-layout">
              <section className="console-panel workspace-primary-panel">
                {workspacePanel === "overview" ? (
                  <>
                    <div className="panel-heading">
                      <div>
                        <p className="auth-kicker">Overview</p>
                        <h3>Everything important about this workspace</h3>
                      </div>
                    </div>
                    <div className="detail-stack">
                      <div className="detail-card detail-card-emphasis">
                        <strong>{selectedWorkspace?.workspace_name ?? "Workspace"}</strong>
                        <span>{selectedWorkspace?.description || "No general description yet."}</span>
                        <small>{selectedWorkspace?.purpose || "No stated purpose yet."}</small>
                      </div>
                      <div className="detail-grid">
                        <button type="button" className="action-tile" onClick={() => setWorkspacePanel("ingest")}>
                          <span className="action-tile-label">Next step</span>
                          <strong>Add knowledge</strong>
                          <small>Upload files, queue URLs, or use a server file path.</small>
                        </button>
                        <button type="button" className="action-tile" onClick={() => setWorkspacePanel("chat")}>
                          <span className="action-tile-label">Launch</span>
                          <strong>Open chat</strong>
                          <small>Ask questions grounded in this workspace’s indexed content.</small>
                        </button>
                        <button type="button" className="action-tile" onClick={() => setWorkspacePanel("members")}>
                          <span className="action-tile-label">Access</span>
                          <strong>Manage members</strong>
                          <small>Review who can access the workspace and invite new people.</small>
                        </button>
                      </div>
                    </div>
                  </>
                ) : null}

                {workspacePanel === "ingest" ? (
                  <>
                    <div className="panel-heading">
                      <div>
                        <p className="auth-kicker">Knowledge intake</p>
                        <h3>Upload content in a simple sequence</h3>
                      </div>
                    </div>
                    <div className="workspace-intake-stack">
                      <form className="stack-form step-card" onSubmit={(event) => event.preventDefault()}>
                        <label className="field-label">Namespace</label>
                        <input
                          value={ingestNamespace}
                          onChange={(event) => setIngestNamespace(event.target.value)}
                          placeholder="aurora"
                        />
                      </form>

                      <form className="stack-form step-card" onSubmit={handleUploadFile}>
                        <label className="field-label">1. Upload file</label>
                        <input
                          type="file"
                          onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                          accept=".txt,.md,.csv,.pdf,.docx,.html,.htm"
                        />
                        <button type="submit">Upload to workspace</button>
                      </form>

                      <form className="stack-form step-card" onSubmit={(event) => handleQueueSource(event, uploadSourceUrl, "url")}>
                        <label className="field-label">2. Add URL</label>
                        <input
                          value={uploadSourceUrl}
                          onChange={(event) => setUploadSourceUrl(event.target.value)}
                          placeholder="https://example.com/policy"
                        />
                        <button type="submit">Queue URL</button>
                      </form>

                      <form className="stack-form step-card" onSubmit={(event) => handleQueueSource(event, uploadSourcePath, "file")}>
                        <label className="field-label">3. Add server file path</label>
                        <input
                          value={uploadSourcePath}
                          onChange={(event) => setUploadSourcePath(event.target.value)}
                          placeholder="aurora-facilities-group/field-ops-assistant/operations-playbook.txt"
                        />
                        <button type="submit">Queue file path</button>
                      </form>
                    </div>
                  </>
                ) : null}

                {workspacePanel === "chat" ? (
                  <>
                    <div className="panel-heading">
                      <div>
                        <p className="auth-kicker">Chat</p>
                        <h3>Ask the workspace</h3>
                      </div>
                    </div>
                    <p className="muted-copy compact-copy">
                      Ask questions only against the active workspace. Answers should stay scoped to this workspace’s documents.
                    </p>
                    <div className="chat-thread">
                      {chatMessages.map((message, index) => (
                        <div
                          key={`${message.role}-${index}`}
                          className={message.role === "assistant" ? "chat-bubble chat-assistant" : "chat-bubble chat-user"}
                        >
                          <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
                          <p>{message.content}</p>
                        </div>
                      ))}
                      {!chatMessages.length ? <p className="muted-copy">Launch the chat by asking a workspace question below.</p> : null}
                    </div>
                    <form className="stack-form" onSubmit={handleChat}>
                      <textarea
                        value={chatDraft}
                        onChange={(event) => setChatDraft(event.target.value)}
                        placeholder="Ask a question about this workspace…"
                        rows={4}
                      />
                      <button type="submit">Send to chat</button>
                    </form>
                    {sources.length ? (
                      <div className="sources-panel">
                        {sources.map((source, index) => (
                          <div key={`${source.source}-${index}`} className="detail-card">
                            <strong>{source.source}</strong>
                            <small>{source.snippet}</small>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </>
                ) : null}

                {workspacePanel === "members" ? (
                  <>
                    <div className="panel-heading">
                      <div>
                        <p className="auth-kicker">Members</p>
                        <h3>Invite people into this workspace</h3>
                      </div>
                    </div>
                    <p className="muted-copy compact-copy">
                      Use organization invites to grant scoped workspace access, then review the current direct workspace members here.
                    </p>
                    {selectedOrg ? (
                      <form className="stack-form" onSubmit={handleInviteMember}>
                        <input value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="Member email" />
                        <input value={inviteName} onChange={(event) => setInviteName(event.target.value)} placeholder="Display name (optional)" />
                        <select value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                          <option value="owner">Owner</option>
                        </select>
                        {inviteRole === "member" ? (
                          <div className="checkbox-list">
                            {workspaces.map((workspace) => (
                              <label key={workspace.workspace_id}>
                                <input
                                  type="checkbox"
                                  checked={inviteWorkspaceIds.includes(workspace.workspace_id)}
                                  onChange={(event) =>
                                    setInviteWorkspaceIds((current) =>
                                      event.target.checked
                                        ? [...current, workspace.workspace_id]
                                        : current.filter((workspaceId) => workspaceId !== workspace.workspace_id)
                                    )
                                  }
                                />
                                <span>{workspace.workspace_name}</span>
                              </label>
                            ))}
                          </div>
                        ) : null}
                        <button type="submit">Invite to organization/workspace</button>
                      </form>
                    ) : (
                      <p className="muted-copy">Select an organization before inviting members.</p>
                    )}
                  </>
                ) : null}
              </section>

              <aside className="page-side">
                <section className="console-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="auth-kicker">Workspace detail</p>
                      <h3>General information</h3>
                    </div>
                  </div>
                  {selectedWorkspace ? (
                    <div className="list-panel">
                      <div className="detail-card detail-card-emphasis">
                        <strong>{selectedWorkspace.workspace_name}</strong>
                        <span>{selectedWorkspace.workspace_type}</span>
                        <small>{selectedWorkspace.workspace_slug}</small>
                      </div>
                      <div className="detail-card">
                        <strong>General information</strong>
                        <span>{selectedWorkspace.description || "No general description yet."}</span>
                        <small>{selectedWorkspace.purpose || "No stated purpose yet."}</small>
                      </div>
                    </div>
                  ) : (
                    <p className="muted-copy">Workspace detail will appear here.</p>
                  )}
                </section>

                <section className="console-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="auth-kicker">Assets</p>
                      <h3>Indexed documents</h3>
                    </div>
                  </div>
                  <div className="list-panel">
                    {documents.map((document) => (
                      <div key={document.document_id} className="detail-card">
                        <strong>{document.source}</strong>
                        <span>{document.source_type}</span>
                        <small>
                          {document.ingestion_status} · {document.chunk_count} chunks
                        </small>
                      </div>
                    ))}
                    {!documents.length ? <p className="muted-copy">No indexed documents yet.</p> : null}
                  </div>
                </section>

                <section className="console-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="auth-kicker">Access</p>
                      <h3>Workspace members</h3>
                    </div>
                  </div>
                  <div className="list-panel">
                    {workspaceMembers.map((member) => (
                      <div key={member.user_id} className="member-row">
                        <div>
                          <strong>{member.display_name || member.email}</strong>
                          <span>{member.email}</span>
                        </div>
                        <small>{member.role}</small>
                      </div>
                    ))}
                    {!workspaceMembers.length ? <p className="muted-copy">No direct workspace members yet.</p> : null}
                  </div>
                </section>
              </aside>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

async function getFreshToken(
  getToken: (options?: { template?: string; skipCache?: boolean }) => Promise<string | null>
): Promise<{ token: string; label: string }> {
  let token: string | null = null;
  let label = "Clerk session token";

  if (clerkJwtTemplate) {
    try {
      token = await getToken({ template: clerkJwtTemplate, skipCache: true });
      label = `Clerk JWT template "${clerkJwtTemplate}"`;
    } catch {
      token = await getToken({ skipCache: true });
      label = `Clerk session token fallback after template "${clerkJwtTemplate}" was unavailable`;
    }
  } else {
    token = await getToken({ skipCache: true });
  }

  if (!token) {
    throw new Error("Clerk did not return a usable session token.");
  }

  return { token, label };
}
